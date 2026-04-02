"""
Season-Wise Seed Parser (season_seed).

Scrapes: https://www.tnagrisnet.tn.gov.in/people_app/Season/index/en
Iteration: district → block → season → crop → result

Actual API chain (from live page inspection):
  1. getBlocks/{district_id}                              → [{id, Block_Name}]
  2. Seasons hardcoded in <select#season>: Adipattam, Kuruvai (value = season name string)
  3. getCrop/{season}/{district_id}/{block_id}            → [{stock_id, stock_name}]
  4. POST result/en: district_id, block_id, season, crop_id (= stock_id)

Result fields: cropName, varietyName, className, aecName, quantity (note: no 'unit' field)
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from tfais.config.settings import (
    SEED_AGRI_BLOCKS_URL,
    SEED_SEASON_ENTRY_URL,
    SEED_SEASON_GET_CROP_URL,
    SEED_SEASON_RESULTS_URL,
)
from tfais.core.http_utils import rate_limit, retry_request
from tfais.core.metadata import safe_parse_number

from .base_angular import BaseAngularSeedParser

log = logging.getLogger(__name__)


@dataclass
class SeasonSeedRecord:
    district_code: str
    district_name: str
    block_code: str
    block_name: str
    season: str                       # e.g. "Kuruvai", "Adipattam"
    crop_name: str                    # cropName from result
    crop_variety: Optional[str]       # varietyName
    seed_class: Optional[str]         # className
    agency_name: Optional[str]        # aecName
    contact_person: Optional[str]     # full_name
    contact_phone: Optional[str]      # user_phone
    quantity_available: Optional[float]
    unit: Optional[str]
    price: Optional[str]              # price
    scraped_at: datetime


class SeasonSeedParser(BaseAngularSeedParser):
    """Parse season-wise seed stock."""

    parser_id = "season_seed"
    ENTRY_URL = SEED_SEASON_ENTRY_URL
    BLOCKS_URL = SEED_AGRI_BLOCKS_URL
    RESULTS_URL = SEED_SEASON_RESULTS_URL

    def __init__(self):
        super().__init__()
        self.seasons = []

    def bootstrap(self) -> list[dict]:
        """Bootstrap session and extract season list from entry page."""
        districts = super().bootstrap()

        html = self.session.get(self.ENTRY_URL, timeout=30).text
        soup = BeautifulSoup(html, "html.parser")
        self.seasons = self._extract_seasons(soup)
        log.debug(f"{self.parser_id}: Found {len(self.seasons)} seasons")

        return districts

    def _extract_seasons(self, soup: BeautifulSoup) -> list[str]:
        """Parse <select#season> → [season_name, ...] (values are name strings)."""
        seasons = []
        select = soup.find("select", {"id": "season"})
        if not select:
            return seasons
        for option in select.find_all("option"):
            val = option.get("value", "").strip()
            if val and val != "":
                seasons.append(val)
        return seasons

    def get_crops(self, season: str, district_code: str, block_code: str) -> list[dict]:
        """
        POST getCrop/{season}/{district_id}/{block_id} → [{stock_id, stock_name}]
        """
        url = f"{SEED_SEASON_GET_CROP_URL}/{season}/{district_code}/{block_code}"
        rate_limit(2.0)
        resp = retry_request(lambda: self.session.post(url, timeout=30), max_retries=3)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            log.warning(f"{self.parser_id}: Failed to decode crops for season {season} block {block_code}")
            return []

    def _fetch_and_parse_block(
        self,
        district_code: str,
        district_name: str,
        block_code: str,
        block_name: str,
    ) -> list[SeasonSeedRecord]:
        """Iterate seasons → crops for this block."""
        records = []

        for season in self.seasons:
            crops = self.get_crops(season, district_code, block_code)
            if not crops:
                log.debug(f"{self.parser_id}: No crops for season {season} in block {block_code}")
                continue

            for crop in crops:
                crop_id = str(crop.get("stock_id") or "")
                crop_name = crop.get("stock_name") or ""

                form_data = {
                    "district_id": district_code,
                    "block_id": block_code,
                    "season": season,
                    "crop_id": crop_id,
                }

                try:
                    html = self.fetch_result(form_data)
                    crop_records = self.parse(
                        html,
                        district_code=district_code,
                        district_name=district_name,
                        block_code=block_code,
                        block_name=block_name,
                        season_name=season,
                        crop_name=crop_name,
                    )
                    records.extend(crop_records)
                except Exception as e:
                    log.warning(
                        f"{self.parser_id}: Error fetching season {season} "
                        f"crop {crop_id} in block {block_code}: {e}"
                    )
                    continue

        return records

    def parse(self, raw_html: str, **context) -> list[SeasonSeedRecord]:
        """
        Extract seed records from ng-init JSON.
        Actual API result fields: cropName, varietyName, aecName, quantity (no unit field)
          season     ← context.season_name
          crop_name  ← item.cropName
          variety    ← item.varietyName
          agency     ← item.aecName
          quantity   ← item.quantity
        """
        records = []

        items = self._extract_ng_init(raw_html, key="seed_list")
        if not items:
            return records

        for item in items:
            try:
                crop_variety = item.get("varietyName") or item.get("variety") or None
                quantity = safe_parse_number(str(item.get("quantity") or item.get("qty") or ""))
                unit = item.get("unit") or item.get("units") or "MT"

                record = SeasonSeedRecord(
                    district_code=context.get("district_code"),
                    district_name=context.get("district_name"),
                    block_code=context.get("block_code"),
                    block_name=context.get("block_name"),
                    season=context.get("season_name", ""),
                    crop_name=item.get("cropName") or context.get("crop_name", ""),
                    crop_variety=crop_variety if crop_variety else None,
                    seed_class=item.get("className") or None,
                    agency_name=item.get("aecName") or item.get("agency_name") or None,
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

    def persist(self, records: list[SeasonSeedRecord], session, run_id: int) -> int:
        from tfais.database.operations import insert_season_seed_batch
        inserted = insert_season_seed_batch(session, records, run_id)
        log.info(f"{self.parser_id}: Persisted {inserted} new season seed records")
        return inserted

    def get_previous_count(self, session) -> int:
        from tfais.database.operations import get_previous_season_seed_count
        return get_previous_season_seed_count(session)
