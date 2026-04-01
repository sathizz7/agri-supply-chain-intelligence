"""
Fertilizer Stock Position Parser

Consolidates the legacy scraper/session_manager.py, scraper/scraper.py,
and parser/card_parser.py into a single self-contained parser.

HTTP workflow: session-based (cookies + CSRF + hidden fields).
Iteration: district → block → POST → ng-init JSON / HTML fallback.

Design ref: docs/subsection_parser_logic.md (Section 1)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

from tfais.config.settings import (
    BASE_URL,
    MAX_RETRIES,
    RATE_LIMIT_SECONDS,
    REQUEST_TIMEOUT,
)
from tfais.core.http_utils import DEFAULT_HEADERS, rate_limit, retry_request
from tfais.core.metadata import extract_last_updated, safe_parse_number

log = logging.getLogger(__name__)

# --- URLs (English-first) ---
STOCK_ENTRY_URL = f"{BASE_URL}/fertilizer/stock/en/20/2020"
STOCK_BLOCKS_URL = f"{BASE_URL}/Fertilizer/getBlocks"
STOCK_RESULTS_URL = f"{BASE_URL}/Fertilizer/result/en"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DealerRecord:
    """Structured output for one dealer card."""
    district_code: str
    district_name_en: str
    district_name_ta: str
    block_code: str
    block_name_en: str
    block_name_ta: str
    dealer_name_en: str
    dealer_name_ta: str
    dealer_code: str
    address: str
    contact: str
    stocks: dict[str, float]       # fertilizer name → quantity in kg
    scraped_at: datetime
    structure_sig: Optional[str] = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Known "no data" Tamil markers
NO_DATA_MARKERS = [
    "தகவல் இல்லை", "முடிவுகள் இல்லை", "தரவு இல்லை",
    "no data", "no records", "no result",
]

ERROR_MARKERS = [
    "login", "session expired", "unauthorized",
    "internal server error", "404", "500",
]

# Card selector chain — most-specific → least-specific.
CARD_SELECTORS = [
    {"tag": "div", "attrs": {"class": "card"},        "label": "Bootstrap card"},
    {"tag": "div", "attrs": {"class": "dealer-card"}, "label": "Custom dealer card"},
    {"tag": "div", "attrs": {"class": "panel"},       "label": "Bootstrap panel"},
    {"tag": "div", "attrs": {"class": "col-md-4"},    "label": "Bootstrap grid col"},
    {"tag": "div", "attrs": {"class": "col-sm-6"},    "label": "Bootstrap grid col-sm"},
    None,  # structural fallback
]


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ParseWarning(Exception):
    """Non-fatal: data was recovered with adjustments."""


class ParseError(Exception):
    """Fatal: this card cannot be parsed at all."""


# Track known structure signatures across the run
_KNOWN_SIGNATURES: set[str] = set()


# ---------------------------------------------------------------------------
# StockPositionParser
# ---------------------------------------------------------------------------

class StockPositionParser:
    """
    Self-contained parser for fertilizer stock position data.

    Owns its HTTP session, parsing logic, validation, and checkpoints.
    """
    parser_id = "stock_position"
    parser_name = "Fertilizer Stock Position"

    # Validation thresholds
    COUNT_DROP_THRESHOLD = 0.5  # flag if records drop by more than 50%

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._csrf_token: Optional[str] = None
        self._hidden_fields: dict = {}
        self._district_counts: dict[str, int] = {}  # for validation

    # ------------------------------------------------------------------
    # Pipeline entry point
    # ------------------------------------------------------------------

    def run(self, db_session_factory, run_id: int, district_filter: list[str] | None = None) -> dict:
        """Full pipeline: fetch → parse → validate → persist."""
        from tfais.database.operations import (
            insert_anomaly_batch,
            upsert_section_metadata,
        )

        raw_results = self.fetch(district_filter)
        records = self.parse(raw_results)

        with db_session_factory() as session:
            anomalies = self.validate(records, session)
            count = self.persist(records, session, run_id)

            if anomalies:
                insert_anomaly_batch(session, run_id, anomalies)

            # Update section metadata
            source_date = self._extract_source_date(raw_results)
            upsert_section_metadata(
                session, "fertilizer", "stock_position", source_date
            )
            session.commit()

        return {
            "parser_id": self.parser_id,
            "records": len(records),
            "persisted": count,
            "anomalies": anomalies,
        }

    # ------------------------------------------------------------------
    # HTTP: Bootstrap
    # ------------------------------------------------------------------

    def bootstrap(self) -> list[dict]:
        """
        GET the entry page to establish session, extract CSRF token,
        and discover district list.

        Returns: [{'code': '1', 'name_ta': '...', 'name_en': '...'}, ...]
        """
        log.info(f"Bootstrapping session from {STOCK_ENTRY_URL}")

        def _do():
            return self.session.get(STOCK_ENTRY_URL, timeout=REQUEST_TIMEOUT)

        resp = retry_request(_do, max_retries=MAX_RETRIES)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Capture CSRF token
        csrf_input = soup.find("input", {"name": "_token"})
        if csrf_input:
            self._csrf_token = csrf_input.get("value", "")

        # Capture all hidden form fields
        for hidden in soup.find_all("input", {"type": "hidden"}):
            name = hidden.get("name", "")
            value = hidden.get("value", "")
            if name:
                self._hidden_fields[name] = value

        # Extract district list
        districts = self._extract_districts(soup)
        log.info(f"Found {len(districts)} districts")
        return districts

    def get_blocks_for_district(self, district_code: str) -> list[dict]:
        """POST to get blocks for a district. Handles JSON and HTML responses."""
        url = f"{STOCK_BLOCKS_URL}/{district_code}"

        def _do():
            return self.session.post(url, timeout=REQUEST_TIMEOUT)

        resp = retry_request(_do, max_retries=MAX_RETRIES)
        resp.raise_for_status()

        # Try JSON first
        try:
            data = resp.json()
            if isinstance(data, list):
                blocks = []
                for item in data:
                    code = str(
                        item.get("subdistrict_id")
                        or item.get("id")
                        or item.get("value")
                        or ""
                    )
                    name_en = str(item.get("subdistrict_name") or item.get("name") or item.get("text") or "")
                    name_ta = str(item.get("tamil_subdistrict_name") or "")
                    if code and code not in ("0", ""):
                        blocks.append({"code": code, "name_en": name_en, "name_ta": name_ta})
                return blocks
        except (ValueError, AttributeError):
            pass

        # Fallback: parse as HTML <option> tags
        soup = BeautifulSoup(resp.text, "lxml")
        blocks = []
        for option in soup.find_all("option"):
            val = option.get("value", "").strip()
            if val and val != "0":
                # HTML fallback (shouldn't occur on /en/ URL, but name is English if present)
                blocks.append({"code": val, "name_en": option.get_text(strip=True), "name_ta": None})
        return blocks

    def fetch_results(self, district_code: str, block_code: str) -> str:
        """POST the search form to get dealer stock results HTML."""
        form_data: dict = {
            "district_id": district_code,
            "block_id": block_code,
            **self._hidden_fields,
        }
        if self._csrf_token:
            form_data["_token"] = self._csrf_token

        def _do():
            return self.session.post(
                STOCK_RESULTS_URL, data=form_data, timeout=REQUEST_TIMEOUT
            )

        resp = retry_request(_do, max_retries=MAX_RETRIES)
        resp.raise_for_status()
        return resp.text

    # ------------------------------------------------------------------
    # Fetch: iterate districts → blocks
    # ------------------------------------------------------------------

    def fetch(self, district_filter: list[str] | None = None) -> list[dict]:
        """
        Full fetch: bootstrap → iterate districts → blocks → POST results.

        Returns list of dicts with raw HTML per (district, block).
        """
        from tfais.database.operations import is_checkpoint_done, mark_checkpoint
        from tfais.database.connection import get_session

        districts = self.bootstrap()

        if district_filter:
            districts = [d for d in districts if d["code"] in district_filter]
            log.info(f"Filtered to {len(districts)} districts")

        results = []

        for district in districts:
            try:
                blocks = self.get_blocks_for_district(district["code"])
                log.info(f"  District {district['name_ta']} ({district['code']}): {len(blocks)} blocks")
            except Exception as exc:
                log.error(f"  FAILED to get blocks for {district['code']}: {exc}")
                continue

            district_dealer_count = 0
            for block in blocks:
                try:
                    html = self.fetch_results(district["code"], block["code"])
                    results.append({
                        "district": district,
                        "block": block,
                        "html": html,
                        "status": "ok",
                    })
                except Exception as exc:
                    log.error(f"    FAIL block {block['code']} in {district['code']}: {exc}")
                    results.append({
                        "district": district,
                        "block": block,
                        "html": "",
                        "status": "error",
                        "error": str(exc),
                    })

                rate_limit(RATE_LIMIT_SECONDS)

        return results

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse(self, raw_results: list[dict]) -> list[DealerRecord]:
        """Parse all raw HTML results into DealerRecords."""
        all_records: list[DealerRecord] = []

        for item in raw_results:
            if item.get("status") != "ok" or not item.get("html"):
                continue

            district = item["district"]
            block = item["block"]
            html = item["html"]

            soup = BeautifulSoup(html, "lxml")
            scraped_at = datetime.now(tz=timezone.utc)

            # Strategy 1: ng-init JSON (preferred)
            records = self._parse_ng_init(soup, district, block, scraped_at)
            if records is not None:
                all_records.extend(records)
                self._district_counts[district["code"]] = (
                    self._district_counts.get(district["code"], 0) + len(records)
                )
                continue

            # Strategy 2: HTML card fallback
            log.debug("ng-init not found — falling back to HTML card parsing")
            records = self._parse_cards(soup, district, block, scraped_at)
            all_records.extend(records)
            self._district_counts[district["code"]] = (
                self._district_counts.get(district["code"], 0) + len(records)
            )

        log.info(f"Total parsed: {len(all_records)} dealer records")
        return all_records

    # ------------------------------------------------------------------
    # Validate
    # ------------------------------------------------------------------

    def validate(self, records: list[DealerRecord], session) -> list[dict]:
        """
        Three-level validation. Returns list of anomaly dicts.
        """
        from tfais.database.operations import get_previous_count

        anomalies = []

        # Run-level: compare count to previous
        prev = get_previous_count(session, self.parser_id)
        if prev > 0 and len(records) < prev * self.COUNT_DROP_THRESHOLD:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "count_drop",
                "detail": f"Dealer count dropped {prev} -> {len(records)}",
                "severity": "error",
            })

        # Page-level: flag districts that went from data → empty
        # (relies on self._district_counts populated during parse)

        return anomalies

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------

    def persist(self, records: list[DealerRecord], session, run_id: int) -> int:
        """Persist all records to the database."""
        from tfais.database.operations import persist_dealer_record

        persisted = 0
        for record in records:
            try:
                count = persist_dealer_record(session, record, run_id)
                persisted += count
            except Exception as exc:
                log.error(f"Failed to persist dealer {record.dealer_code}: {exc}")

        session.commit()
        log.info(f"Persisted {persisted} stock records from {len(records)} dealers")
        return persisted

    # ------------------------------------------------------------------
    # ng-init JSON parsing (Strategy 1)
    # ------------------------------------------------------------------

    def _parse_ng_init(
        self,
        soup: BeautifulSoup,
        district: dict,
        block: dict,
        scraped_at: datetime,
    ) -> list[DealerRecord] | None:
        """
        Extract dealer data from the ng-init attribute.
        Returns list of DealerRecords if ng-init found, None if not present.
        """
        tag = soup.find(attrs={"ng-init": True})
        if not tag:
            return None

        raw = tag.get("ng-init", "")
        if not raw.startswith("fert_list="):
            log.warning(f"Unexpected ng-init value (not fert_list=...): {raw[:80]}")
            return None

        json_str = raw[len("fert_list="):]
        # Collapse literal newlines embedded in JSON string values
        json_str = json_str.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")

        try:
            data: dict = json.loads(json_str)
        except json.JSONDecodeError as exc:
            log.error(f"Failed to parse ng-init JSON: {exc}")
            _save_snapshot(json_str[:2000], district.get("code", ""), block.get("code", ""), str(exc))
            return []

        # Site returns either {"0": {...}, "1": {...}} or [{...}, {...}]
        if isinstance(data, list):
            items = enumerate(data)
        else:
            items = data.items()

        records: list[DealerRecord] = []
        for _idx, item in items:
            try:
                stocks: dict[str, float] = {}
                for fert_name, qty_str in (item.get("fert") or {}).items():
                    parsed = safe_parse_number(str(qty_str).replace(",", ""))
                    # Values are in tonnes → convert to kg
                    qty_kg = (parsed * 1000) if parsed is not None else 0.0
                    stocks[fert_name] = qty_kg

                sig = _compute_structure_signature(list(stocks.keys()), 1) if stocks else None
                if sig:
                    _check_signature(sig, list(stocks.keys()))

                records.append(DealerRecord(
                    district_code=district["code"],
                    district_name_en=district.get("name_en", ""),
                    district_name_ta=district.get("name_ta", ""),
                    block_code=block["code"],
                    block_name_en=block.get("name_en", ""),
                    block_name_ta=block.get("name_ta", ""),
                    dealer_name_en=str(item.get("delar_name") or item.get("dealer_name") or "").strip(),
                    dealer_name_ta=str(item.get("tamil_agency") or "").strip(),
                    dealer_code=str(item.get("dealer_id") or "").strip(),
                    address=str(item.get("address") or item.get("tamil_address") or "").strip(),
                    contact=str(item.get("mobile_number") or "").strip(),
                    stocks=stocks,
                    scraped_at=scraped_at,
                    structure_sig=sig,
                ))
            except Exception as exc:
                log.error(f"Failed to parse dealer item {_idx}: {exc}", exc_info=True)
                continue

        log.info(
            f"ng-init: parsed {len(records)} dealers in "
            f"{district.get('name_ta', district['code'])} > "
            f"{block.get('name_ta', block['code'])}"
        )
        return records

    # ------------------------------------------------------------------
    # HTML card parsing (Strategy 2 — fallback)
    # ------------------------------------------------------------------

    def _parse_cards(
        self,
        soup: BeautifulSoup,
        district: dict,
        block: dict,
        scraped_at: datetime,
    ) -> list[DealerRecord]:
        """Original HTML card parser — used if ng-init is absent."""

        # Step 1: Triage
        status = _triage_page(soup)

        if status == "EMPTY":
            log.info(f"No dealers in {district.get('name_ta', district['code'])} > {block.get('name_ta', block['code'])}")
            return []

        if status == "ERROR":
            log.error(f"Error page for district={district['code']} block={block['code']}")
            _save_snapshot(str(soup)[:5000], district.get("code", ""), block.get("code", ""), "ERROR_PAGE")
            return []

        # Step 2: Discover cards
        cards = _discover_cards(soup)
        if not cards:
            log.warning(f"HAS_RESULTS but no cards found for district={district['code']} block={block['code']}")
            _save_snapshot(str(soup)[:5000], district.get("code", ""), block.get("code", ""), "NO_CARDS_FOUND")
            return []

        # Step 3: Parse each card
        records: list[DealerRecord] = []
        for card in cards:
            try:
                record = self._parse_single_card(card, district, block, scraped_at)
                if record is not None:
                    records.append(record)
            except ParseError as exc:
                log.error(f"Card ParseError: {exc}")
                _save_snapshot(str(card), district.get("code", ""), block.get("code", ""), str(exc))
            except Exception as exc:
                log.error(f"Unexpected card error: {exc}", exc_info=True)
                _save_snapshot(str(card), district.get("code", ""), block.get("code", ""), str(exc))

        log.info(
            f"Parsed {len(records)}/{len(cards)} cards in "
            f"{district.get('name_ta', district['code'])} > {block.get('name_ta', block['code'])}"
        )
        return records

    def _parse_single_card(
        self, card: Tag, district: dict, block: dict, scraped_at: datetime,
    ) -> Optional[DealerRecord]:
        """Parse a single dealer card element."""
        identity = _extract_dealer_identity(card)
        if not identity["name"]:
            return None

        address = _extract_address(card)
        contact = _extract_contact(card)

        table = _find_stock_table(card)
        stocks: dict[str, float] = {}
        structure_sig: Optional[str] = None

        if table:
            classified = _classify_rows(table)
            headers = _extract_column_headers(classified)
            value_rows = classified.get("value_rows", [])

            if headers and value_rows:
                first_value_row = value_rows[0]
                raw_values = [td.get_text(strip=True) for td in first_value_row.find_all(["td", "th"])]
                headers, raw_values = _validate_and_align(headers, raw_values)
                stocks = _map_stock_data(headers, raw_values)
                structure_sig = _compute_structure_signature(headers, len(value_rows))
                _check_signature(structure_sig, headers)

        return DealerRecord(
            district_code=district["code"],
            district_name_en=district.get("name_en", ""),
            district_name_ta=district.get("name_ta", ""),
            block_code=block["code"],
            block_name_en=block.get("name_en", ""),
            block_name_ta=block.get("name_ta", ""),
            dealer_name_en=identity["name"],
            dealer_name_ta="",  # HTML fallback doesn't have Tamil name
            dealer_code=identity["code"],
            address=address,
            contact=contact,
            stocks=stocks,
            scraped_at=scraped_at,
            structure_sig=structure_sig,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_districts(self, soup: BeautifulSoup) -> list[dict]:
        """Parse district <option> tags from the main page <select> dropdown."""
        districts = []
        select = (
            soup.find("select", id="district_id")
            or soup.find("select", {"name": "district_id"})
            or soup.find("select", {"id": lambda x: x and "district" in x.lower()})
            or soup.find("select", {"name": lambda x: x and "district" in x.lower()})
        )

        if not select:
            for sel in soup.find_all("select"):
                opts = [o for o in sel.find_all("option") if o.get("value", "").strip().isdigit()]
                if len(opts) >= 10:
                    select = sel
                    break

        if not select:
            log.warning("Could not find district <select>")
            return districts

        for option in select.find_all("option"):
            val = option.get("value", "").strip()
            if val and val not in ("0", ""):
                # The /en/ URL returns English district names in the <select>
                districts.append({"code": val, "name_en": option.get_text(strip=True), "name_ta": None})

        return districts

    def _extract_source_date(self, raw_results: list[dict]) -> Optional[datetime]:
        """Extract source update date from any result page HTML."""
        for item in raw_results:
            if item.get("html"):
                source_date = extract_last_updated(item["html"])
                if source_date:
                    return datetime.combine(source_date, datetime.min.time(), tzinfo=timezone.utc)
        return None


# ---------------------------------------------------------------------------
# Module-level helper functions (migrated from card_parser.py)
# ---------------------------------------------------------------------------

def _triage_page(soup: BeautifulSoup) -> str:
    """Classify page as HAS_RESULTS | EMPTY | ERROR."""
    page_text = soup.get_text(separator=" ", strip=True)
    page_lower = page_text.lower()

    if any(m in page_lower for m in NO_DATA_MARKERS):
        return "EMPTY"
    if any(m in page_lower for m in ERROR_MARKERS):
        return "ERROR"
    if soup.find("table"):
        return "HAS_RESULTS"
    if len(page_text) > 100:
        return "ERROR"
    return "EMPTY"


def _discover_cards(soup: BeautifulSoup) -> list[Tag]:
    """Find dealer card containers using prioritized selector chain."""
    for selector in CARD_SELECTORS:
        if selector is None:
            candidates = []
            for div in soup.find_all("div"):
                inner_tables = div.find_all("table", recursive=True)
                if len(inner_tables) == 1:
                    inner_divs = div.find_all("div", recursive=False)
                    if len(inner_divs) <= 2:
                        candidates.append(div)
            if candidates:
                return candidates
        else:
            cards = soup.find_all(selector["tag"], attrs=selector["attrs"])
            if cards:
                return cards
    return []


def _extract_dealer_identity(card: Tag) -> dict:
    """Extract dealer name and code from card header."""
    HEADER_FINDERS = [
        lambda c: c.find(class_=re.compile(r"card-header|card-title|header|title", re.I)),
        lambda c: c.find(["h3", "h4", "h5", "h6", "strong", "b"]),
        lambda c: c,
    ]

    text = ""
    for finder in HEADER_FINDERS:
        element = finder(card)
        if element:
            candidate = element.get_text(strip=True)
            if candidate and len(candidate) > 3:
                text = candidate
                break

    if not text:
        return {"name": "", "code": ""}

    code_match = re.search(r"\((\d{4,})\)", text)
    if code_match:
        code = code_match.group(1)
        name = text[: code_match.start()].strip().rstrip("(").strip()
    else:
        code = ""
        name = text.strip()

    return {"name": name, "code": code}


def _extract_address(card: Tag) -> str:
    """Extract dealer address from card."""
    body = card.find(class_=re.compile(r"card-body|body|content|text", re.I)) or card
    for p in body.find_all("p"):
        text = p.get_text(strip=True)
        if not text or text.startswith("*") or len(text) <= 3:
            continue
        if re.match(r"^[\d\s\-\+\(\)]+$", text):
            continue
        return text
    for tag in body.find_all(["span", "div", "small"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 10 and not re.match(r"^[\d\s\-\+]+$", text):
            return text
    return ""


def _extract_contact(card: Tag) -> str:
    """Extract 10-digit Indian mobile number from card text."""
    card_text = card.get_text()
    match = re.search(r"[6-9]\d{9}", card_text)
    return match.group(0) if match else ""


def _find_stock_table(card: Tag) -> Optional[Tag]:
    """Find the fertilizer stock table within a dealer card."""
    tables = card.find_all("table")
    if not tables:
        return None
    if len(tables) == 1:
        return tables[0]
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if any(_is_numeric_text(c.get_text(strip=True)) for c in cells):
                return table
    return max(tables, key=lambda t: len(t.find_all("tr")))


def _is_numeric_text(text: str) -> bool:
    """True if text represents a number."""
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return False
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _classify_rows(table: Tag) -> dict:
    """Classify rows by cell-majority content (header vs value vs other)."""
    result: dict[str, list] = {"header_rows": [], "value_rows": [], "other_rows": []}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        cell_texts = [c.get_text(strip=True) for c in cells]
        non_empty = [t for t in cell_texts if t]
        if not non_empty:
            continue
        numeric_count = sum(1 for t in non_empty if _is_numeric_text(t))
        ratio = numeric_count / len(non_empty)
        if ratio > 0.5:
            result["value_rows"].append(row)
        elif ratio == 0.0:
            result["header_rows"].append(row)
        else:
            result["other_rows"].append(row)
    return result


def _extract_column_headers(classified: dict) -> list[str]:
    """Extract column headers from the last header row."""
    header_rows = classified.get("header_rows", [])
    if not header_rows:
        return []
    last_row = header_rows[-1]
    cells = last_row.find_all(["td", "th"])
    return [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]


def _validate_and_align(headers: list[str], values: list[str]) -> tuple[list[str], list[str]]:
    """Validate and align header/value counts."""
    if not headers:
        raise ParseError("Empty headers")
    if not values:
        raise ParseError("Empty values")
    if not any(_is_numeric_text(v) for v in values):
        raise ParseError(f"No numeric values in data row: {values}")
    if len(headers) != len(values):
        min_len = min(len(headers), len(values))
        log.warning(f"Header/value mismatch ({len(headers)} vs {len(values)}). Truncating to {min_len}.")
        headers = headers[:min_len]
        values = values[:min_len]
    return headers, values


def _map_stock_data(headers: list[str], raw_values: list[str]) -> dict[str, float]:
    """Map fertilizer names → quantities."""
    result = {}
    for h, v in zip(headers, raw_values):
        parsed = safe_parse_number(v)
        result[h.strip()] = parsed if parsed is not None else 0.0
    return result


def _compute_structure_signature(headers: list[str], num_value_rows: int) -> str:
    """MD5 fingerprint of table structure for site-change detection."""
    sig_input = "|".join(sorted(headers)) + f"|rows={num_value_rows}"
    return hashlib.md5(sig_input.encode("utf-8")).hexdigest()


def _check_signature(sig: str, headers: list[str]) -> None:
    """Warn if an unrecognised table structure appears."""
    if _KNOWN_SIGNATURES and sig not in _KNOWN_SIGNATURES:
        log.warning(f"NEW TABLE STRUCTURE — sig={sig}, headers={headers}")
    _KNOWN_SIGNATURES.add(sig)


def _save_snapshot(html_fragment: str, district: str, block: str, error: str) -> None:
    """Save failed card HTML to logs/failed_cards/ for offline debugging."""
    try:
        os.makedirs("logs/failed_cards", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"logs/failed_cards/stock_{district}_{block}_{ts}.html"
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(f"<!-- ERROR: {error} -->\n")
            fh.write(html_fragment)
    except Exception as exc:
        log.warning(f"Could not save snapshot: {exc}")
