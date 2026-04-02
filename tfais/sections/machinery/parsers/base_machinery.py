"""
Base class for CHC Mobile machinery parsers (Tractor, Woman Mechanics, Drone).

Architecture difference from seed parsers:
- No CodeIgniter session (no ci_session cookie, no CSRF token)
- Pure stateless GET JSON APIs — no HTML scraping
- Simpler bootstrap: just fetch districts from JSON endpoint
- Results come directly as JSON arrays (not embedded in ng-init HTML)
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import sessionmaker

from tfais.core.http_utils import DEFAULT_HEADERS, rate_limit, retry_request
from tfais.database.operations import (
    insert_anomaly_batch,
    is_checkpoint_done,
    mark_checkpoint,
    upsert_section_metadata,
)

log = logging.getLogger(__name__)


class BaseMachineryParser:
    """Base class for CHC Mobile machinery parsers."""

    parser_id = "machinery_base"
    section_id = "machinery"

    DISTRICTS_URL = None   # Must be set by subclass
    BLOCKS_URL = None      # Must be set by subclass (None for drone — district-only)
    RESULTS_URL = None     # Must be set by subclass

    COUNT_DROP_THRESHOLD = 0.5  # Flag if count < 50% of previous run

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.scraped_at = datetime.now(tz=timezone.utc)

    def get_districts(self) -> list[dict]:
        """
        GET DISTRICTS_URL → [{id, name}] or [{code, name}].
        Returns list of districts with 'code' and 'name' keys normalised.
        """
        rate_limit(1.0)
        resp = retry_request(
            lambda: self.session.get(self.DISTRICTS_URL, timeout=30),
            max_retries=3,
        )
        resp.raise_for_status()

        try:
            data = resp.json()
            if not isinstance(data, list):
                log.warning(f"{self.parser_id}: Unexpected districts response type")
                return []
            return self._normalize_districts(data)
        except json.JSONDecodeError:
            log.warning(f"{self.parser_id}: Failed to decode districts JSON")
            return []

    def get_blocks(self, district_id: str) -> list[dict]:
        """
        GET BLOCKS_URL/{district_id} → [{id, name}].
        Returns list of blocks with 'code' and 'name' keys normalised.
        """
        url = f"{self.BLOCKS_URL}/{district_id}"
        rate_limit(1.0)

        resp = retry_request(
            lambda: self.session.get(url, timeout=30),
            max_retries=3,
        )
        resp.raise_for_status()

        try:
            data = resp.json()
            if not isinstance(data, list):
                return []
            return self._normalize_blocks(data)
        except json.JSONDecodeError:
            log.warning(f"{self.parser_id}: Failed to decode blocks JSON for {district_id}")
            return []

    def get_results(self, **kwargs) -> list[dict]:
        """
        Fetch results JSON for the given parameters.
        Subclasses override this with their specific endpoint and field names.
        Returns list of raw dicts from the API.
        """
        raise NotImplementedError(f"{self.parser_id} must implement get_results()")

    def _normalize_districts(self, data: list[dict]) -> list[dict]:
        """
        Normalise district API response to [{'code': ..., 'name': ...}].
          getDistricts (tractor/drone): DistrictCode, DistrictName
          getWDSDistricts (wm):         DistrictId, District
        """
        normalised = []
        for item in data:
            code = (
                item.get("DistrictCode") or
                item.get("DistrictId") or
                item.get("id") or item.get("Id") or ""
            )
            name = (
                item.get("DistrictName") or
                item.get("District") or
                item.get("name") or item.get("Name") or
                str(code)
            )
            if code:
                normalised.append({"code": str(code), "name": str(name)})
        return normalised

    def _normalize_blocks(self, data: list[dict]) -> list[dict]:
        """
        Normalise block API response to [{'code': ..., 'name': ...}].
          getBlocks (tractor): BlockCode, BlockName  (also contains DistrictCode — must not grab that)
          getWDSBlocks (wm):   BlockId, Block
        """
        normalised = []
        for item in data:
            code = (
                item.get("BlockCode") or
                item.get("BlockId") or
                item.get("id") or item.get("Id") or ""
            )
            name = (
                item.get("BlockName") or
                item.get("Block") or
                item.get("name") or item.get("Name") or
                str(code)
            )
            if code:
                normalised.append({"code": str(code), "name": str(name)})
        return normalised

    def parse(self, raw_items: list[dict], **context):
        """
        Map raw API dicts to typed record objects.
        Must be overridden by subclass — returns list of dataclass records.
        """
        raise NotImplementedError(f"{self.parser_id} must implement parse()")

    def validate(self, records: list, prev_count: int) -> list[dict]:
        """
        Basic validation: empty result and count drop detection.
        Returns list of anomaly dicts.
        """
        anomalies = []
        if not records:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "empty_result",
                "detail": f"No machinery records found for {self.parser_id}",
                "severity": "warning",
            })
            return anomalies

        if prev_count > 0 and len(records) < prev_count * self.COUNT_DROP_THRESHOLD:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "count_drop",
                "detail": (
                    f"Count dropped from {prev_count} to {len(records)} "
                    f"({100 * len(records) / prev_count:.1f}%)"
                ),
                "severity": "warning",
            })
        return anomalies

    def persist(self, records: list, session, run_id: int) -> int:
        """
        Persist records to DB.
        Must be overridden by subclass to call the correct insert function.
        """
        raise NotImplementedError(f"{self.parser_id} must implement persist()")

    def run(
        self,
        db_session_factory: sessionmaker,
        run_id: int,
        district_filter: Optional[list[str]] = None,
    ) -> dict:
        """
        Full pipeline: get districts, iterate, fetch results, parse, validate, persist.
        Returns {parser_id, records, persisted, anomalies}
        """
        result = {
            "parser_id": self.parser_id,
            "records": [],
            "persisted": 0,
            "anomalies": [],
        }

        try:
            districts = self.get_districts()
            if not districts:
                log.warning(f"{self.parser_id}: No districts returned")
                result["anomalies"].append({
                    "parser_id": self.parser_id,
                    "anomaly_type": "empty_districts",
                    "detail": "get_districts() returned empty list",
                    "severity": "error",
                })
                return result

            all_records = []

            self._iterate(
                districts=districts,
                district_filter=district_filter,
                db_session_factory=db_session_factory,
                run_id=run_id,
                all_records=all_records,
            )

            # Validate
            anomalies = self.validate(all_records, prev_count=0)

            # Persist
            with db_session_factory() as session:
                persisted = self.persist(all_records, session, run_id)
                if anomalies:
                    insert_anomaly_batch(session, run_id, anomalies)
                upsert_section_metadata(session, self.section_id, self.parser_id)
                session.commit()

            result["records"] = all_records
            result["persisted"] = persisted
            result["anomalies"] = anomalies

        except Exception as e:
            log.error(f"{self.parser_id}: Fatal error in run(): {e}", exc_info=True)
            result["anomalies"].append({
                "parser_id": self.parser_id,
                "anomaly_type": "fatal_error",
                "detail": str(e),
                "severity": "error",
            })

        return result

    def _iterate(
        self,
        districts: list[dict],
        district_filter: Optional[list[str]],
        db_session_factory: sessionmaker,
        run_id: int,
        all_records: list,
    ) -> None:
        """
        Default iteration: district → block → results.
        DroneOwnersParser overrides this (district-only, no block loop).
        """
        for district in districts:
            district_code = district["code"]
            if district_filter and district_code not in district_filter:
                continue

            district_name = district["name"]
            log.info(f"{self.parser_id}: Processing district {district_code} ({district_name})")

            blocks = self.get_blocks(district_code)
            if not blocks:
                log.warning(f"{self.parser_id}: No blocks for district {district_code}")
                continue

            for block in blocks:
                block_code = block["code"]
                block_name = block["name"]
                work_unit_key = f"{district_code}:{block_code}"

                with db_session_factory() as session:
                    if is_checkpoint_done(session, run_id, self.parser_id, work_unit_key):
                        log.debug(f"{self.parser_id}: Skipping done checkpoint {work_unit_key}")
                        continue

                try:
                    raw_items = self.get_results(
                        district_code=district_code,
                        block_code=block_code,
                    )
                    records = self.parse(
                        raw_items,
                        district_code=district_code,
                        district_name=district_name,
                        block_code=block_code,
                        block_name=block_name,
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
