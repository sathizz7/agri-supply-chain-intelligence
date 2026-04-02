"""
Women PLF (Producer Livelihood Federation) Machinery Hiring Parser (women_plf).

Scrapes: http://115.243.209.84/chc/Mobile/woman_mechanics/en/20
Page title: "Magalir Thittam - Implements Hiring / Women PLF"

Each record is a Women's SHG/PLF group that provides farm implements for hire.
Iteration: district → block → PLF list
API: GET /getWDSDistricts, GET /getWDSBlocks/{district_id}, GET /getWDCMechanics/{block_id}

Key API field mapping (37 fields total, capturing 8 relevant ones):
  WomenPLF          → plf_name
  PLF_President     → mobile_number
  ContactAddress    → contact_address
  MachineryProcurred→ machinery_procured
  MachineryAvailable→ available_count
  panchayat         → panchayat
  Block/BlockId     → block_name/block_code
  District/DistrictId → district_name/district_code
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from tfais.config.settings import (
    MACHINERY_RATE_LIMIT,
    MACHINERY_WDS_BLOCKS_URL,
    MACHINERY_WDS_DISTRICTS_URL,
    MACHINERY_WDS_RESULTS_URL,
)
from tfais.core.http_utils import rate_limit, retry_request

from .base_machinery import BaseMachineryParser

log = logging.getLogger(__name__)


@dataclass
class WomenPLFRecord:
    district_code: str               # DistrictId from API
    district_name: str               # District
    block_code: str                  # BlockId
    block_name: str                  # Block
    plf_name: Optional[str]          # WomenPLF — group name
    mobile_number: Optional[str]     # PLF_President
    contact_address: Optional[str]   # ContactAddress
    machinery_procured: Optional[str] # MachineryProcurred — full list string
    available_count: Optional[str]   # MachineryAvailable
    panchayat: Optional[str]         # panchayat
    scraped_at: datetime


class WomenPLFParser(BaseMachineryParser):
    """Parse Women's PLF machinery hiring data from CHC Mobile portal."""

    parser_id = "women_plf"
    DISTRICTS_URL = MACHINERY_WDS_DISTRICTS_URL
    BLOCKS_URL = MACHINERY_WDS_BLOCKS_URL
    RESULTS_URL = MACHINERY_WDS_RESULTS_URL

    def get_results(self, district_code: str = None, block_code: str = None, **kwargs) -> list[dict]:
        """GET /getWDCMechanics/{block_id} → [{WomenPLF, PLF_President, ContactAddress, ...}]"""
        url = f"{self.RESULTS_URL}/{block_code}"
        rate_limit(MACHINERY_RATE_LIMIT)

        resp = retry_request(
            lambda: self.session.get(url, timeout=30),
            max_retries=3,
        )
        resp.raise_for_status()

        try:
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception:
            log.warning(f"{self.parser_id}: Failed to decode results JSON for block {block_code}")
            return []

    def parse(self, raw_items: list[dict], **context) -> list[WomenPLFRecord]:
        """Map raw API items to WomenPLFRecord objects."""
        records = []
        # Fall back to context values if item doesn't carry district/block
        ctx_district_code = context.get("district_code", "")
        ctx_district_name = context.get("district_name", "")
        ctx_block_code = context.get("block_code", "")
        ctx_block_name = context.get("block_name", "")

        for item in raw_items:
            try:
                record = WomenPLFRecord(
                    district_code=item.get("DistrictId") or ctx_district_code,
                    district_name=item.get("District") or ctx_district_name,
                    block_code=item.get("BlockId") or ctx_block_code,
                    block_name=item.get("Block") or ctx_block_name,
                    plf_name=item.get("WomenPLF") or None,
                    mobile_number=item.get("PLF_President") or None,
                    contact_address=item.get("ContactAddress") or None,
                    machinery_procured=item.get("MachineryProcurred") or None,
                    available_count=item.get("MachineryAvailable") or None,
                    panchayat=item.get("panchayat") or None,
                    scraped_at=self.scraped_at,
                )
                records.append(record)
            except Exception as e:
                log.warning(f"{self.parser_id}: Error parsing item {item}: {e}")
                continue

        return records

    def persist(self, records: list[WomenPLFRecord], session, run_id: int) -> int:
        from tfais.database.operations import insert_women_plf_batch
        return insert_women_plf_batch(session, records, run_id)
