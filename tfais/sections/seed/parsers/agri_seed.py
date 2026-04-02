"""
Agriculture Department Seed Parser (agri_seed).

Scrapes: https://www.tnagrisnet.tn.gov.in/people_app/Seed/seed_gov/en
Iteration: district → block → crop
Entry page contains crop list in <select#crop_id>.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from tfais.config.settings import (
    SEED_AGRI_BLOCKS_URL,
    SEED_AGRI_ENTRY_URL,
    SEED_AGRI_RESULTS_URL,
)
from tfais.core.metadata import safe_parse_number

from .base_angular import BaseAngularSeedParser

log = logging.getLogger(__name__)


@dataclass
class AgriSeedRecord:
    district_code: str
    district_name: str
    block_code: str
    block_name: str
    crop_name: str
    crop_variety: Optional[str]
    seed_class: Optional[str]
    agency_name: Optional[str]
    contact_person: Optional[str]
    contact_phone: Optional[str]
    quantity_available: Optional[float]
    unit: Optional[str]
    price: Optional[str]
    scraped_at: datetime


class AgriSeedParser(BaseAngularSeedParser):
    """Parse agriculture department seed stock."""

    parser_id = "agri_seed"
    ENTRY_URL = SEED_AGRI_ENTRY_URL
    BLOCKS_URL = SEED_AGRI_BLOCKS_URL
    RESULTS_URL = SEED_AGRI_RESULTS_URL

    def __init__(self):
        super().__init__()
        self.crops = []

    def bootstrap(self) -> list[dict]:
        """Bootstrap and extract crop list from entry page."""
        districts = super().bootstrap()

        # Extract crops from <select#crop_id>
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        html = self.session.get(self.ENTRY_URL, timeout=30).text
        soup = BeautifulSoup(html, "html.parser")
        self.crops = self._extract_crops(soup)
        log.debug(f"{self.parser_id}: Found {len(self.crops)} crops")

        return districts

    def _extract_crops(self, soup: BeautifulSoup) -> list[dict]:
        """Parse <select#crop_id> → [{code, name}]."""
        crops = []
        select = soup.find("select", {"id": "crop_id"})
        if not select:
            return crops

        for option in select.find_all("option"):
            code = option.get("value", "").strip()
            name = option.get_text(strip=True)
            if code and code != "":
                crops.append({"code": code, "name": name})

        return crops

    def _fetch_and_parse_block(
        self,
        district_code: str,
        district_name: str,
        block_code: str,
        block_name: str,
    ) -> list[AgriSeedRecord]:
        """Iterate crops for this block, fetch and parse results."""
        records = []

        for crop in self.crops:
            crop_code = crop.get("code")
            crop_name = crop.get("name", "")

            form_data = {
                "district_id": district_code,
                "block_id": block_code,
                "crop_id": crop_code,
            }

            try:
                html = self.fetch_result(form_data)
                crop_records = self.parse(
                    html,
                    district_code=district_code,
                    district_name=district_name,
                    block_code=block_code,
                    block_name=block_name,
                )
                records.extend(crop_records)
            except Exception as e:
                log.warning(
                    f"{self.parser_id}: Error fetching crop {crop_code} in {block_code}: {e}"
                )
                continue

        return records

    def parse(self, raw_html: str, **context) -> list[AgriSeedRecord]:
        """
        Extract seed records from ng-init JSON.
        Actual API field names (from live inspection):
          crop_name ← cropName
          crop_variety ← varietyName
          agency_name ← aecName (Agricultural Extension Centre)
          quantity_available ← quantity
          unit ← unit (may be None — default "MT")
        """
        records = []

        items = self._extract_ng_init(raw_html, key="seed_list")
        if not items:
            return records

        for item in items:
            try:
                crop_variety = item.get("varietyName") or item.get("variety") or item.get("variety_name")
                quantity = safe_parse_number(str(item.get("quantity") or item.get("qty") or ""))
                unit = item.get("unit") or "MT"

                record = AgriSeedRecord(
                    district_code=context.get("district_code"),
                    district_name=context.get("district_name"),
                    block_code=context.get("block_code"),
                    block_name=context.get("block_name"),
                    crop_name=item.get("cropName") or item.get("crop_name") or item.get("crop", ""),
                    crop_variety=crop_variety if crop_variety else None,
                    seed_class=item.get("className") or None,
                    agency_name=item.get("aecName") or item.get("agency_name") or item.get("agency") or None,
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

    def persist(self, records: list[AgriSeedRecord], session, run_id: int) -> int:
        from tfais.database.operations import insert_agri_seed_batch
        inserted = insert_agri_seed_batch(session, records, run_id)
        log.info(f"{self.parser_id}: Persisted {inserted} new agri seed records")
        return inserted

    def get_previous_count(self, session) -> int:
        from tfais.database.operations import get_previous_agri_seed_count
        return get_previous_agri_seed_count(session)
