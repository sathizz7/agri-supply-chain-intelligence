"""
Private Agriculture Drone Owner Parser (drone_owners).

Scrapes: http://115.243.209.84/chc/Mobile/drone/en/20
Iteration: district only (NO block level)
API: GET /getDistricts (shared), GET /loadDrone/{district_id}
Response fields: ownerName, mobileNumber, NoOfDrone, implements

Key difference from tractor/woman_mechanics:
  - No block loop — one API call per district
  - Checkpoint key: "district:{district_code}" (not district:block)
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import asyncio

import aiohttp

from tfais.config.settings import (
    MACHINERY_DISTRICTS_URL,
    MACHINERY_DRONE_RESULTS_URL,
    MACHINERY_RATE_LIMIT,
    MAX_CONCURRENT_DISTRICTS,
)
from tfais.core.http_utils import rate_limit, rate_limit_async, retry_request, retry_request_async
from tfais.database.operations import (
    is_checkpoint_done,
    mark_checkpoint,
)

from .base_machinery import BaseMachineryParser

log = logging.getLogger(__name__)


@dataclass
class DroneRecord:
    district_code: str
    district_name: str
    block_code: Optional[str]    # BlockCode from API
    block_name: Optional[str]    # Block (village/block name) from API
    owner_name: Optional[str]    # ownerName from API
    mobile_number: Optional[str]
    scraped_at: datetime


class DroneOwnersParser(BaseMachineryParser):
    """Parse Private Agriculture Drone Owner data — district-only (no block loop)."""

    parser_id = "drone_owners"
    DISTRICTS_URL = MACHINERY_DISTRICTS_URL
    BLOCKS_URL = None   # Not used — drone is district-only
    RESULTS_URL = MACHINERY_DRONE_RESULTS_URL

    def get_results(self, district_code: str = None, **kwargs) -> list[dict]:
        """GET /loadDrone/{district_id} → [{ownerName, mobileNumber, NoOfDrone, implements}]"""
        url = f"{self.RESULTS_URL}/{district_code}"
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
            log.warning(f"{self.parser_id}: Failed to decode results JSON for district {district_code}")
            return []

    def parse(self, raw_items: list[dict], **context) -> list[DroneRecord]:
        """
        Map raw API items to DroneRecord objects.
        API returns Block/BlockCode per record (not passed via context).
        """
        records = []
        district_code = context.get("district_code", "")
        district_name = context.get("district_name", "")

        for item in raw_items:
            try:
                record = DroneRecord(
                    district_code=item.get("DistrictCode") or district_code,
                    district_name=item.get("District") or district_name,
                    block_code=item.get("BlockCode") or None,
                    block_name=item.get("Block") or None,
                    owner_name=item.get("ownerName") or item.get("OwnerName") or None,
                    mobile_number=item.get("MobileNumber") or item.get("mobileNumber") or None,
                    scraped_at=self.scraped_at,
                )
                records.append(record)
            except Exception as e:
                log.warning(f"{self.parser_id}: Error parsing item {item}: {e}")
                continue

        return records

    async def get_results_async(
        self, aio_session: aiohttp.ClientSession, district_code: str = None, **kwargs
    ) -> list[dict]:
        """Async GET /loadDrone/{district_id}"""
        url = f"{self.RESULTS_URL}/{district_code}"
        await rate_limit_async(MACHINERY_RATE_LIMIT)
        async with await retry_request_async(
            lambda: aio_session.get(url, timeout=aiohttp.ClientTimeout(total=30)),
        ) as resp:
            resp.raise_for_status()
            try:
                data = await resp.json(content_type=None)
                return data if isinstance(data, list) else []
            except Exception:
                log.warning(f"{self.parser_id}: Failed to decode results JSON for district {district_code}")
                return []

    def persist(self, records: list[DroneRecord], session, run_id: int) -> int:
        from tfais.database.operations import insert_drone_batch
        return insert_drone_batch(session, records, run_id)

    def _iterate(
        self,
        districts: list[dict],
        district_filter,
        db_session_factory,
        run_id: int,
        all_records: list,
    ) -> None:
        """
        Override: district-only iteration — no block loop.
        Checkpoint key: "district:{district_code}"
        """
        for district in districts:
            district_code = district["code"]
            if district_filter and district_code not in district_filter:
                continue

            district_name = district["name"]
            work_unit_key = f"district:{district_code}"

            log.info(f"{self.parser_id}: Processing district {district_code} ({district_name})")

            with db_session_factory() as session:
                if is_checkpoint_done(session, run_id, self.parser_id, work_unit_key):
                    log.debug(f"{self.parser_id}: Skipping done checkpoint {work_unit_key}")
                    continue

            try:
                raw_items = self.get_results(district_code=district_code)
                records = self.parse(
                    raw_items,
                    district_code=district_code,
                    district_name=district_name,
                )
                all_records.extend(records)

                with db_session_factory() as session:
                    mark_checkpoint(
                        session, run_id, self.parser_id, work_unit_key,
                        status="done", records_found=len(records),
                    )
                    session.commit()

            except Exception as e:
                log.error(f"{self.parser_id}: Error at {work_unit_key}: {e}")
                with db_session_factory() as session:
                    mark_checkpoint(
                        session, run_id, self.parser_id, work_unit_key,
                        status="error", error_message=str(e),
                    )
                    session.commit()

    async def _iterate_async(
        self,
        aio_session: aiohttp.ClientSession,
        districts: list[dict],
        district_filter,
        db_session_factory,
        run_id: int,
        all_records: list,
    ) -> None:
        """
        Override: district-only concurrent iteration.
        Checkpoint key: "district:{district_code}"
        """
        from .base_machinery import _check_checkpoint, _mark_checkpoint_done, _mark_checkpoint_error

        sem = asyncio.Semaphore(MAX_CONCURRENT_DISTRICTS)

        async def _process(district: dict) -> None:
            district_code = district["code"]
            if district_filter and district_code not in district_filter:
                return

            async with sem:
                district_name = district["name"]
                work_unit_key = f"district:{district_code}"

                log.info(f"{self.parser_id}: [async] Processing district {district_code} ({district_name})")

                done = await asyncio.to_thread(
                    _check_checkpoint, db_session_factory, run_id, self.parser_id, work_unit_key
                )
                if done:
                    log.debug(f"{self.parser_id}: Skipping done checkpoint {work_unit_key}")
                    return

                try:
                    raw_items = await self.get_results_async(aio_session, district_code=district_code)
                    records = self.parse(raw_items, district_code=district_code, district_name=district_name)
                    all_records.extend(records)
                    await asyncio.to_thread(
                        _mark_checkpoint_done,
                        db_session_factory, run_id, self.parser_id, work_unit_key, len(records),
                    )
                except Exception as e:
                    log.error(f"{self.parser_id}: Error at {work_unit_key}: {e}")
                    await asyncio.to_thread(
                        _mark_checkpoint_error,
                        db_session_factory, run_id, self.parser_id, work_unit_key, str(e),
                    )

        results = await asyncio.gather(*[_process(d) for d in districts], return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                log.error(f"{self.parser_id}: District task raised: {r}")
