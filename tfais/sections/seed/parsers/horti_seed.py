"""
Horticulture Department Seed Parser (horti_seed).

Scrapes: https://www.tnagrisnet.tn.gov.in/people_app/Horti_seed/index/en
Iteration: district → block → stock_type → stock → result

Actual API chain (from live page inspection):
  1. getBlocks/{district_id}          → [{id, Block_Name, ...}]
  2. loadStockType/{block_id}         → [{stock_type_id, stock_type_name}]
  3. loadStock/{stock_type_id}/{block_id} → [{stock_id, stock_name, units}]
  4. POST result/en: district_id, block_id, stock_type_id, stock_id

Result fields: cropName, stock_type_name (via context), className, varietyName, aecName, quantity, units
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from tfais.config.settings import (
    SEED_AGRI_BLOCKS_URL,
    SEED_HORTI_ENTRY_URL,
    SEED_HORTI_LOAD_STOCK_URL,
    SEED_HORTI_RESULTS_URL,
    SEED_HORTI_STOCK_TYPE_URL,
)
from tfais.core.http_utils import rate_limit, retry_request
from tfais.core.metadata import safe_parse_number

from .base_angular import BaseAngularSeedParser

log = logging.getLogger(__name__)


@dataclass
class HortiSeedRecord:
    district_code: str
    district_name: str
    block_code: str
    block_name: str
    stock_type: Optional[str]        # stock_type_name (e.g. "Fruits Seedlings")
    input_name: Optional[str]        # cropName from result (e.g. "Acidlime")
    seed_class: Optional[str]        # className (e.g. "seedlings")
    crop_variety: Optional[str]      # varietyName (e.g. "PKM-1")
    agency_name: Optional[str]       # aecName
    contact_person: Optional[str]    # full_name
    contact_phone: Optional[str]     # user_phone
    quantity_available: Optional[float]
    unit: Optional[str]
    price: Optional[str]             # price
    scraped_at: datetime


class HortiSeedParser(BaseAngularSeedParser):
    """Parse horticulture department seed stock."""

    parser_id = "horti_seed"
    ENTRY_URL = SEED_HORTI_ENTRY_URL
    BLOCKS_URL = SEED_AGRI_BLOCKS_URL
    RESULTS_URL = SEED_HORTI_RESULTS_URL

    def get_stock_types(self, block_code: str) -> list[dict]:
        """
        POST loadStockType/{block_id} → [{stock_type_id, stock_type_name}]
        """
        url = f"{SEED_HORTI_STOCK_TYPE_URL}/{block_code}"
        rate_limit(2.0)
        resp = retry_request(lambda: self.session.post(url, timeout=30), max_retries=3)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            log.warning(f"{self.parser_id}: Failed to decode stock types for block {block_code}")
            return []

    def get_stocks(self, stock_type_id: str, block_code: str) -> list[dict]:
        """
        POST loadStock/{stock_type_id}/{block_id} → [{stock_id, stock_name, units}]
        """
        url = f"{SEED_HORTI_LOAD_STOCK_URL}/{stock_type_id}/{block_code}"
        rate_limit(2.0)
        resp = retry_request(lambda: self.session.post(url, timeout=30), max_retries=3)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            log.warning(f"{self.parser_id}: Failed to decode stocks for type {stock_type_id} block {block_code}")
            return []

    def _fetch_and_parse_block(
        self,
        district_code: str,
        district_name: str,
        block_code: str,
        block_name: str,
    ) -> list[HortiSeedRecord]:
        """Iterate stock_types → stocks for this block, fetch results."""
        records = []

        stock_types = self.get_stock_types(block_code)
        if not stock_types:
            log.warning(f"{self.parser_id}: No stock types for block {block_code}")
            return records

        for st in stock_types:
            stock_type_id = str(st.get("stock_type_id") or "")
            stock_type_name = st.get("stock_type_name") or ""

            stocks = self.get_stocks(stock_type_id, block_code)
            if not stocks:
                log.debug(f"{self.parser_id}: No stocks for type {stock_type_id} in block {block_code}")
                continue

            for stock in stocks:
                stock_id = str(stock.get("stock_id") or "")
                stock_name = stock.get("stock_name") or ""

                form_data = {
                    "district_id": district_code,
                    "block_id": block_code,
                    "stock_type_id": stock_type_id,
                    "stock_id": stock_id,
                }

                try:
                    html = self.fetch_result(form_data)
                    crop_records = self.parse(
                        html,
                        district_code=district_code,
                        district_name=district_name,
                        block_code=block_code,
                        block_name=block_name,
                        stock_type_name=stock_type_name,
                        stock_name=stock_name,
                    )
                    records.extend(crop_records)
                except Exception as e:
                    log.warning(
                        f"{self.parser_id}: Error fetching {stock_type_id}/{stock_id} "
                        f"in block {block_code}: {e}"
                    )
                    continue

        return records

    def parse(self, raw_html: str, **context) -> list[HortiSeedRecord]:
        """
        Extract seed records from ng-init JSON.
        Actual API result fields: cropName, units, aecName, quantity, varietyName
          stock_type  ← context.stock_type_name
          input_name  ← item.cropName (the specific stock, e.g. "Acidlime")
          agency_name ← item.aecName
          quantity    ← item.quantity
          unit        ← item.units
        """
        records = []

        items = self._extract_ng_init(raw_html, key="seed_list")
        if not items:
            return records

        for item in items:
            try:
                quantity = safe_parse_number(str(item.get("quantity") or item.get("qty") or ""))
                unit = item.get("units") or item.get("unit") or "Nos"

                record = HortiSeedRecord(
                    district_code=context.get("district_code"),
                    district_name=context.get("district_name"),
                    block_code=context.get("block_code"),
                    block_name=context.get("block_name"),
                    stock_type=context.get("stock_type_name") or None,
                    input_name=item.get("cropName") or context.get("stock_name") or None,
                    seed_class=item.get("className") or None,
                    crop_variety=item.get("varietyName") or None,
                    agency_name=item.get("aecName") or item.get("agency") or None,
                    contact_person=item.get("full_name") or None,
                    contact_phone=item.get("user_phone") or None,
                    quantity_available=quantity,
                    unit=unit,
                    price=item.get("price") or None,
                    scraped_at=self.scraped_at,
                )
                records.append(record)
            except Exception as e:
                log.warning(f"{self.parser_id}: Error parsing item {item}: {e}")
                continue

        return records

    def persist(self, records: list[HortiSeedRecord], session, run_id: int) -> int:
        from tfais.database.operations import insert_horti_seed_batch
        inserted = insert_horti_seed_batch(session, records, run_id)
        log.info(f"{self.parser_id}: Persisted {inserted} new horti seed records")
        return inserted

    def get_previous_count(self, session) -> int:
        from tfais.database.operations import get_previous_horti_seed_count
        return get_previous_horti_seed_count(session)
