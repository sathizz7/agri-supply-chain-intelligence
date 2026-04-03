"""
Private Tractor Owner Parser (private_tractor).

Scrapes: http://115.243.209.84/chc/Mobile/privateOwner/en/20
Iteration: district → block → owner list
API: GET /getDistricts, GET /getBlocks/{district_id}, GET /getPrivateOwners/{block_id}
Response fields: OwnerName, MobileNumber, RegistrationNo, MakerModel, MachineryName, ImplementName
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

import aiohttp

from tfais.config.settings import (
    MACHINERY_BLOCKS_URL,
    MACHINERY_DISTRICTS_URL,
    MACHINERY_RATE_LIMIT,
    MACHINERY_TRACTOR_RESULTS_URL,
)
from tfais.core.http_utils import rate_limit, rate_limit_async, retry_request, retry_request_async
from tfais.database.operations import insert_anomaly_batch, upsert_section_metadata

from .base_machinery import BaseMachineryParser

log = logging.getLogger(__name__)


@dataclass
class TractorRecord:
    district_code: str
    district_name: str
    block_code: str
    block_name: str
    owner_name: Optional[str]
    mobile_number: Optional[str]
    registration_no: Optional[str]
    maker_model: Optional[str]
    machinery_name: Optional[str]
    implement_name: Optional[str]
    scraped_at: datetime


class PrivateTractorParser(BaseMachineryParser):
    """Parse Private Tractor Owner data from CHC Mobile portal."""

    parser_id = "private_tractor"
    DISTRICTS_URL = MACHINERY_DISTRICTS_URL
    BLOCKS_URL = MACHINERY_BLOCKS_URL
    RESULTS_URL = MACHINERY_TRACTOR_RESULTS_URL

    def get_results(self, district_code: str = None, block_code: str = None, **kwargs) -> list[dict]:
        """GET /getPrivateOwners/{block_id} → [{OwnerName, MobileNumber, ...}]"""
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

    def parse(self, raw_items: list[dict], **context) -> list[TractorRecord]:
        """Map raw API items to TractorRecord objects."""
        records = []
        district_code = context.get("district_code", "")
        district_name = context.get("district_name", "")
        block_code = context.get("block_code", "")
        block_name = context.get("block_name", "")

        for item in raw_items:
            try:
                record = TractorRecord(
                    district_code=item.get("DistrictCode") or district_code,
                    district_name=item.get("District") or district_name,
                    block_code=item.get("BlockCode") or block_code,
                    block_name=item.get("Block") or block_name,
                    owner_name=item.get("OwnerName") or None,
                    mobile_number=item.get("MobileNumber") or None,
                    registration_no=item.get("RegistrationNo") or None,
                    maker_model=item.get("MakeModel") or None,           # API field is MakeModel
                    machinery_name=item.get("NameOfManufacturer") or None,
                    implement_name=item.get("AvailableImplements") or None,
                    scraped_at=self.scraped_at,
                )
                records.append(record)
            except Exception as e:
                log.warning(f"{self.parser_id}: Error parsing item {item}: {e}")
                continue

        return records

    async def get_results_async(
        self, aio_session: aiohttp.ClientSession, district_code: str = None, block_code: str = None, **kwargs
    ) -> list[dict]:
        """Async GET /getPrivateOwners/{block_id}"""
        url = f"{self.RESULTS_URL}/{block_code}"
        await rate_limit_async(MACHINERY_RATE_LIMIT)
        async with await retry_request_async(
            lambda: aio_session.get(url, timeout=aiohttp.ClientTimeout(total=30)),
        ) as resp:
            resp.raise_for_status()
            try:
                data = await resp.json(content_type=None)
                return data if isinstance(data, list) else []
            except Exception:
                log.warning(f"{self.parser_id}: Failed to decode results JSON for block {block_code}")
                return []

    def persist(self, records: list[TractorRecord], session, run_id: int) -> int:
        from tfais.database.operations import insert_tractor_batch
        return insert_tractor_batch(session, records, run_id)
