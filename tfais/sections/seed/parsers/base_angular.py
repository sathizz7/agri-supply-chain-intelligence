"""
Base class for AngularJS-based seed parsers (Agri, Horti, Season-Wise).

Shared logic:
- CodeIgniter session bootstrap (ci_session cookie, CSRF token)
- ng-init JSON extraction from HTML
- District and block fetching
- Checkpoint management
- Validation and persistence
"""
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session, sessionmaker

from tfais.core.http_utils import DEFAULT_HEADERS, rate_limit, retry_request
from tfais.database.operations import (
    insert_anomaly_batch,
    is_checkpoint_done,
    mark_checkpoint,
    upsert_section_metadata,
)

log = logging.getLogger(__name__)


class BaseAngularSeedParser:
    """Base class for AngularJS-based seed parsers."""

    parser_id = "seed_base"
    section_id = "seed"

    ENTRY_URL = None    # Must be set by subclass
    BLOCKS_URL = None   # Must be set by subclass
    RESULTS_URL = None  # Must be set by subclass

    COUNT_DROP_THRESHOLD = 0.5  # Flag if count < 50% of previous run

    def __init__(self):
        self.session = None
        self.csrf_token = None
        self.districts = []
        self.scraped_at = datetime.now(tz=timezone.utc)

    def bootstrap(self) -> list[dict]:
        """
        Bootstrap session: GET entry URL, capture ci_session cookie, CSRF token, hidden fields.
        Returns list of available districts: [{code, name_en, name_ta}]
        """
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

        html = retry_request(
            lambda: self.session.get(self.ENTRY_URL, timeout=30),
            max_retries=3,
        ).text

        soup = BeautifulSoup(html, "html.parser")

        # Extract CSRF token if present (ng-init hidden field)
        csrf_input = soup.find("input", {"name": "csrf_token"})
        if csrf_input:
            self.csrf_token = csrf_input.get("value", "")

        # Extract districts from <select#district_id>
        self.districts = self._extract_districts(soup)
        log.debug(f"{self.parser_id}: Found {len(self.districts)} districts")

        return self.districts

    def get_blocks(self, district_code: str) -> list[dict]:
        """
        POST to BLOCKS_URL/{district_code} to get available blocks.
        Returns [{code, name_en, name_ta}] where code = block id for POST params.
        Seed API block fields: id, Block_Name, TBlock_Name, Block_Code (3-letter abbrev).
        """
        url = f"{self.BLOCKS_URL}/{district_code}"

        resp = retry_request(
            lambda: self.session.post(url, timeout=30),
            max_retries=3,
        )
        resp.raise_for_status()

        try:
            raw = resp.json()
            if not isinstance(raw, list):
                return []
            blocks = []
            for b in raw:
                block_id = str(b.get("id") or "").strip()
                name_en = b.get("Block_Name") or b.get("name") or ""
                name_ta = b.get("TBlock_Name") or b.get("tamil_block_name") or name_en
                if block_id:
                    blocks.append({"code": block_id, "name_en": name_en, "name_ta": name_ta})
            return blocks
        except json.JSONDecodeError:
            log.warning(f"Failed to decode blocks JSON for {district_code}")
            return []

    def fetch_result(self, form_data: dict) -> str:
        """
        POST to RESULTS_URL with form data (district, block, crop/season/type, etc).
        Returns raw HTML response.
        """
        rate_limit(2.0)  # Seed rate limit

        resp = retry_request(
            lambda: self.session.post(self.RESULTS_URL, data=form_data, timeout=30),
            max_retries=3,
        )
        resp.raise_for_status()
        return resp.text

    def _extract_districts(self, soup: BeautifulSoup) -> list[dict]:
        """Parse <select#district_id> → [{code, name_en}]."""
        districts = []
        select = soup.find("select", {"id": "district_id"})
        if not select:
            return districts

        for option in select.find_all("option"):
            code = option.get("value", "").strip()
            name_en = option.get_text(strip=True)
            if code and code != "":
                districts.append({"code": code, "name_en": name_en, "name_ta": name_en})

        return districts

    def _extract_ng_init(self, html: str, key: str = "seed_list") -> list[dict]:
        """
        Extract JSON from ng-init attribute.
        Two-step strategy for robustness:
        1. Regex on raw HTML (handles malformed attribute encoding)
        2. Fallback to BeautifulSoup find
        """
        records = []

        # Step 1: Regex extraction (more robust for malformed HTML)
        pattern = rf'ng-init=["\']?{key}=(\[.*?\])["\']?'
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                json_str = match.group(1)
                records = json.loads(json_str)
                return records
            except (json.JSONDecodeError, IndexError):
                pass

        # Step 2: BeautifulSoup fallback
        try:
            soup = BeautifulSoup(html, "html.parser")
            elem = soup.find(attrs={"ng-init": True})
            if elem:
                ng_init = elem.get("ng-init", "")
                match = re.search(rf'{key}=(\[.*?\])', ng_init, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    records = json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass

        return records

    def parse(self, raw_html: str, **context) -> list:
        """
        Parse raw HTML to extract seed records.
        Subclasses override this to handle subsection-specific field mapping.
        """
        raise NotImplementedError(f"{self.parser_id} must implement parse()")

    def validate(self, records: list, prev_count: int) -> list[dict]:
        """
        Validation: count drop detection, empty-stock flagging.
        prev_count: record count from the previous completed run (0 if no prior run).
        Returns list of anomaly dicts.
        """
        anomalies = []

        if not records:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "empty_result",
                "detail": f"No seed records found for {self.parser_id}",
                "severity": "warning",
            })
            return anomalies

        if prev_count > 0 and len(records) < prev_count * self.COUNT_DROP_THRESHOLD:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "count_drop",
                "detail": f"Count dropped from {prev_count} to {len(records)} ({100 * len(records) / prev_count:.1f}%)",
                "severity": "warning",
            })

        return anomalies

    def persist(self, records: list, session: Session, run_id: int) -> int:
        """Subclasses must override — call the appropriate typed insert function."""
        raise NotImplementedError(f"{self.parser_id} must implement persist()")

    def run(
        self,
        db_session_factory: sessionmaker,
        run_id: int,
        district_filter: Optional[list[str]] = None,
    ) -> dict:
        """
        Full pipeline: bootstrap, iterate districts/blocks, fetch, parse, validate, persist.
        Returns {parser_id, records, persisted, anomalies}
        """
        result = {
            "parser_id": self.parser_id,
            "records": [],
            "persisted": 0,
            "anomalies": [],
        }

        try:
            # Bootstrap session and get districts
            self.bootstrap()

            all_records = []
            all_anomalies = []

            # Iterate districts
            for district in self.districts:
                district_code = district.get("code")
                if district_filter and district_code not in district_filter:
                    continue

                district_name = district.get("name_en", "")
                log.info(f"{self.parser_id}: Processing district {district_code}")

                # Get blocks
                blocks = self.get_blocks(district_code)
                if not blocks:
                    log.warning(f"{self.parser_id}: No blocks for district {district_code}")
                    continue

                # Iterate blocks
                for block in blocks:
                    block_code = block.get("code", "")
                    block_name = block.get("name_en", "")

                    # Checkpoint: block level
                    work_unit_key = f"district:{district_code}:block:{block_code}"

                    with db_session_factory() as session:
                        if is_checkpoint_done(session, run_id, self.parser_id, work_unit_key):
                            log.debug(f"{self.parser_id}: Skipping completed checkpoint {work_unit_key}")
                            continue

                    # Subclass-specific iteration (crop, season/input, etc)
                    # Subclass calls fetch_result() with appropriate form_data
                    try:
                        records = self._fetch_and_parse_block(
                            district_code, district_name, block_code, block_name
                        )
                        all_records.extend(records)

                        with db_session_factory() as session:
                            mark_checkpoint(
                                session,
                                run_id,
                                self.parser_id,
                                work_unit_key,
                                status="done",
                                records_found=len(records),
                            )
                            session.commit()
                    except Exception as e:
                        log.error(f"{self.parser_id}: Error processing {work_unit_key}: {e}")
                        with db_session_factory() as session:
                            mark_checkpoint(
                                session,
                                run_id,
                                self.parser_id,
                                work_unit_key,
                                status="error",
                                error_message=str(e),
                            )
                            session.commit()
                        continue

            # Validate all records (subclass provides previous count)
            with db_session_factory() as session:
                prev_count = self.get_previous_count(session)
            all_anomalies = self.validate(all_records, prev_count)

            # Persist records
            with db_session_factory() as session:
                persisted = self.persist(all_records, session, run_id)

                # Insert anomalies
                if all_anomalies:
                    insert_anomaly_batch(session, run_id, all_anomalies)

                # Upsert section metadata
                upsert_section_metadata(session, self.section_id, self.parser_id)
                session.commit()

            result["records"] = all_records
            result["persisted"] = persisted
            result["anomalies"] = all_anomalies

        except Exception as e:
            log.error(f"{self.parser_id}: Fatal error in run(): {e}", exc_info=True)
            result["anomalies"].append({
                "parser_id": self.parser_id,
                "anomaly_type": "fatal_error",
                "detail": str(e),
                "severity": "error",
            })

        return result

    def get_previous_count(self, session: Session) -> int:
        """Return previous run record count for count-drop validation. Subclasses override."""
        return 0

    def _fetch_and_parse_block(
        self,
        district_code: str,
        district_name: str,
        block_code: str,
        block_name: str,
    ) -> list:
        """
        Subclass-specific: iterate crops/seasons/inputs and fetch results.
        Must be overridden by AgriSeedParser, HortiSeedParser, SeasonSeedParser.
        """
        raise NotImplementedError(f"{self.parser_id} must implement _fetch_and_parse_block()")
