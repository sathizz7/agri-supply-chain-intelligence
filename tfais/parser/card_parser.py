"""
Phase 2: Card Parser

Parses raw HTML from POST responses into structured dealer records.

ACTUAL SITE BEHAVIOUR (discovered during live inspection):
  The results page is AngularJS-rendered. All dealer data is server-injected
  as a JSON object inside an ng-init attribute on a wrapper <div>:

    <div ng-init='fert_list={"2": {"tamil_agency": "...", "dealer_id": "...",
                                    "fert": {"யூரியா": "0.65", ...}, ...}, ...}'>

  The AngularJS controller is empty — it just binds this inline data.
  No Playwright / JS execution needed.

  JSON stock values are in TONNES; we multiply by 1000 to store as kg.

Pipeline (revised):
  HTML → find ng-init div → parse JSON → per-dealer extraction
       → List[DealerRecord]

The original card-based parser (triage → discover → per-card HTML) is retained
as a fallback for pages that don't contain ng-init data.

Design ref: docs/card_parser.md, docs/revised_HLD.md
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup, Tag

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DealerRecord:
    """Structured output for one dealer card."""
    district_code: str
    district_name: str
    block_code: str
    block_name: str
    dealer_name: str
    dealer_code: str
    address: str
    contact: str
    stocks: dict[str, float]       # fertilizer name (as-is) → quantity kg
    scraped_at: datetime
    structure_sig: Optional[str] = None


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ParseWarning(Exception):
    """Non-fatal: data was recovered with adjustments (truncation etc.)."""


class ParseError(Exception):
    """Fatal: this card cannot be parsed at all."""


# ---------------------------------------------------------------------------
# Card selector chain
# ---------------------------------------------------------------------------

# Ordered most-specific → least-specific.
# First selector that returns results wins.
# None sentinel triggers structural fallback.
CARD_SELECTORS = [
    {"tag": "div", "attrs": {"class": "card"},        "label": "Bootstrap card"},
    {"tag": "div", "attrs": {"class": "dealer-card"}, "label": "Custom dealer card"},
    {"tag": "div", "attrs": {"class": "panel"},       "label": "Bootstrap panel"},
    {"tag": "div", "attrs": {"class": "col-md-4"},    "label": "Bootstrap grid col"},
    {"tag": "div", "attrs": {"class": "col-sm-6"},    "label": "Bootstrap grid col-sm"},
    None,  # structural fallback
]

# Known "no data" Tamil markers
NO_DATA_MARKERS = [
    "தகவல் இல்லை",
    "முடிவுகள் இல்லை",
    "தரவு இல்லை",
    "no data",
    "no records",
    "no result",
]

ERROR_MARKERS = [
    "login",
    "session expired",
    "unauthorized",
    "internal server error",
    "404",
    "500",
]

# Track known structure signatures across the run
_KNOWN_SIGNATURES: set[str] = set()


# ---------------------------------------------------------------------------
# CardParser class
# ---------------------------------------------------------------------------

class CardParser:
    """
    Parses dealer card HTML into DealerRecord objects.

    Usage:
        parser = CardParser()
        records = parser.parse(html_string, district_dict, block_dict)
    """

    def parse(
        self,
        html: str,
        district: dict,
        block: dict,
    ) -> list[DealerRecord]:
        """
        Master entry point. Takes raw POST response HTML.

        Strategy:
          1. Try ng-init JSON extraction (fast, structured — matches live site)
          2. Fall back to HTML card parsing if ng-init not found
        """
        soup = BeautifulSoup(html, "lxml")
        scraped_at = datetime.now(tz=timezone.utc)

        # ── Strategy 1: ng-init JSON (preferred) ────────────────────────
        records = self._parse_ng_init(soup, district, block, scraped_at)
        if records is not None:
            return records

        # ── Strategy 2: HTML card fallback ───────────────────────────────
        log.debug("ng-init not found — falling back to HTML card parsing")
        return self._parse_cards(soup, district, block, scraped_at)

    # ------------------------------------------------------------------
    # Strategy 1: ng-init JSON parsing
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

        The JSON structure (live site):
          {
            "<index>": {
              "tamil_agency":  "<dealer name in Tamil>",
              "dealer_id":     "<numeric dealer code>",
              "tamil_address": "<address>",
              "delar_name":    "<English name — note typo in key>",
              "mobile_number": "<10-digit phone>",
              "fert": {
                "<fertilizer name>": "<quantity in tonnes as string>",
                ...
              }
            },
            ...
          }

        Stock quantities are in TONNES; stored as KG (×1000).
        """
        tag = soup.find(attrs={"ng-init": True})
        if not tag:
            return None

        raw = tag.get("ng-init", "")
        if not raw.startswith("fert_list="):
            log.warning(f"Unexpected ng-init value (not fert_list=...): {raw[:80]}")
            return None

        json_str = raw[len("fert_list="):]
        try:
            data: dict = json.loads(json_str)
        except json.JSONDecodeError as exc:
            log.error(f"Failed to parse ng-init JSON: {exc}")
            _save_snapshot(json_str[:2000], district.get("code", ""), block.get("code", ""), str(exc))
            return []

        records: list[DealerRecord] = []
        for _idx, item in data.items():
            try:
                stocks: dict[str, float] = {}
                for fert_name, qty_str in (item.get("fert") or {}).items():
                    try:
                        qty_kg = float(str(qty_str).replace(",", "")) * 1000
                    except ValueError:
                        qty_kg = 0.0
                    stocks[fert_name] = qty_kg

                # Structure hash over fertilizer names
                sig = compute_structure_signature(list(stocks.keys()), 1) if stocks else None
                if sig:
                    _check_signature(sig, list(stocks.keys()))

                records.append(DealerRecord(
                    district_code=district["code"],
                    district_name=district.get("name_ta", ""),
                    block_code=block["code"],
                    block_name=block.get("name_ta", ""),
                    dealer_name=str(item.get("tamil_agency") or "").strip(),
                    dealer_code=str(item.get("dealer_id") or "").strip(),
                    address=str(item.get("tamil_address") or item.get("address") or "").strip(),
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
    # Strategy 2: HTML card parsing (fallback)
    # ------------------------------------------------------------------

    def _parse_cards(
        self,
        soup: BeautifulSoup,
        district: dict,
        block: dict,
        scraped_at: datetime,
    ) -> list[DealerRecord]:
        """Original HTML card parser — used if ng-init is absent."""

        # ── Step 1: Triage ──────────────────────────────────────────────
        status = triage_page(soup)

        if status == "EMPTY":
            log.info(
                f"No dealers in {district.get('name_ta', district['code'])} "
                f"> {block.get('name_ta', block['code'])}"
            )
            return []

        if status == "ERROR":
            log.error(
                f"Error page for district={district['code']} block={block['code']}"
            )
            _save_snapshot(
                str(soup)[:5000],
                district.get("code", ""),
                block.get("code", ""),
                "ERROR_PAGE",
            )
            return []

        # ── Step 2: Discover cards ──────────────────────────────────────
        cards = discover_cards(soup)

        if not cards:
            log.warning(
                f"HAS_RESULTS but no cards found for "
                f"district={district['code']} block={block['code']} "
                f"— selector chain may need updating"
            )
            _save_snapshot(
                str(soup)[:5000],
                district.get("code", ""),
                block.get("code", ""),
                "NO_CARDS_FOUND",
            )
            return []

        # ── Step 3: Parse each card in isolation ───────────────────────
        records: list[DealerRecord] = []

        for card in cards:
            try:
                record = self._parse_card(card, district, block, scraped_at)
                if record is not None:
                    records.append(record)
            except ParseError as exc:
                log.error(f"Card ParseError: {exc}")
                _save_snapshot(
                    str(card),
                    district.get("code", ""),
                    block.get("code", ""),
                    str(exc),
                )
            except Exception as exc:
                log.error(f"Unexpected card error: {exc}", exc_info=True)
                _save_snapshot(
                    str(card),
                    district.get("code", ""),
                    block.get("code", ""),
                    str(exc),
                )

        log.info(
            f"Parsed {len(records)}/{len(cards)} cards "
            f"in {district.get('name_ta', district['code'])} "
            f"> {block.get('name_ta', block['code'])}"
        )
        return records

    # ------------------------------------------------------------------
    # Private: single card
    # ------------------------------------------------------------------

    def _parse_card(
        self,
        card: Tag,
        district: dict,
        block: dict,
        scraped_at: datetime,
    ) -> Optional[DealerRecord]:
        """Parse a single dealer card element. Returns None for non-dealer divs."""

        # 3a. Dealer identity
        identity = extract_dealer_identity(card)
        if not identity["name"]:
            return None  # not a dealer card (e.g. wrapper div)

        # 3b. Address
        address = extract_address(card)

        # 3c. Contact
        contact = extract_contact(card)

        # 3d. Stock table
        table = find_stock_table(card)
        stocks: dict[str, float] = {}
        structure_sig: Optional[str] = None

        if table:
            # 3e. Row classification
            classified = classify_rows(table)

            # 3f+3g. Headers and values
            headers = extract_column_headers(classified)
            value_rows = classified.get("value_rows", [])

            if headers and value_rows:
                first_value_row = value_rows[0]
                raw_values = [
                    td.get_text(strip=True)
                    for td in first_value_row.find_all(["td", "th"])
                ]

                # Validate + align (may raise ParseError)
                headers, raw_values = validate_and_align(headers, raw_values)

                # Map to dict
                stocks = map_stock_data(headers, raw_values)

                # 3h. Structure hash
                structure_sig = compute_structure_signature(headers, len(value_rows))
                _check_signature(structure_sig, headers)

        return DealerRecord(
            district_code=district["code"],
            district_name=district.get("name_ta", ""),
            block_code=block["code"],
            block_name=block.get("name_ta", ""),
            dealer_name=identity["name"],
            dealer_code=identity["code"],
            address=address,
            contact=contact,
            stocks=stocks,
            scraped_at=scraped_at,
            structure_sig=structure_sig,
        )


# ---------------------------------------------------------------------------
# Step 1: Page triage
# ---------------------------------------------------------------------------

def triage_page(soup: BeautifulSoup) -> str:
    """
    Classify the POST response page before any card parsing.

    Returns:
        'HAS_RESULTS' — page has dealer data
        'EMPTY'       — no dealers in this block (legitimate)
        'ERROR'       — session expired, error page, unexpected content
    """
    page_text = soup.get_text(separator=" ", strip=True)
    page_lower = page_text.lower()

    if any(m in page_lower for m in NO_DATA_MARKERS):
        return "EMPTY"

    if any(m in page_lower for m in ERROR_MARKERS):
        return "ERROR"

    if soup.find("table"):
        return "HAS_RESULTS"

    # Has content but no tables
    if len(page_text) > 100:
        return "ERROR"

    return "EMPTY"


# ---------------------------------------------------------------------------
# Step 2: Card discovery
# ---------------------------------------------------------------------------

def discover_cards(soup: BeautifulSoup) -> list[Tag]:
    """
    Find all dealer card container elements using a prioritized selector chain.
    First match wins. Falls back to structural heuristic.
    """
    for selector in CARD_SELECTORS:
        if selector is None:
            # Structural fallback: any div containing exactly one <table>
            candidates = []
            for div in soup.find_all("div"):
                inner_tables = div.find_all("table", recursive=True)
                if len(inner_tables) == 1:
                    # Make sure it's not a giant wrapper (check for nested divs)
                    inner_divs = div.find_all("div", recursive=False)
                    if len(inner_divs) <= 2:
                        candidates.append(div)
            if candidates:
                log.info(
                    f"Card discovery: structural fallback, found {len(candidates)} cards"
                )
                return candidates
        else:
            cards = soup.find_all(selector["tag"], attrs=selector["attrs"])
            if cards:
                log.info(
                    f"Card discovery: matched '{selector['label']}', "
                    f"found {len(cards)} cards"
                )
                return cards

    log.warning("Card discovery: no selector matched — page structure may have changed")
    return []


# ---------------------------------------------------------------------------
# Step 3a: Dealer identity
# ---------------------------------------------------------------------------

def extract_dealer_identity(card: Tag) -> dict:
    """
    Extract dealer name and code from card header.

    Expected: 'தத்தூர் வேளாண்மை கூட்டுறவு கடன் சங்கம் (999210)'
    Returns:  {'name': 'தத்தூர்...', 'code': '999210'}
    """
    HEADER_FINDERS = [
        lambda c: c.find(class_=re.compile(r"card-header|card-title|header|title", re.I)),
        lambda c: c.find(["h3", "h4", "h5", "h6", "strong", "b"]),
        lambda c: c,  # last resort: full card text
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

    # Code = 4+ digit number in parentheses
    code_match = re.search(r"\((\d{4,})\)", text)
    if code_match:
        code = code_match.group(1)
        name = text[: code_match.start()].strip().rstrip("(").strip()
    else:
        code = ""
        name = text.strip()

    return {"name": name, "code": code}


# ---------------------------------------------------------------------------
# Step 3b: Address
# ---------------------------------------------------------------------------

def extract_address(card: Tag) -> str:
    """Extract dealer address — first non-header, non-phone paragraph in card."""
    body = card.find(class_=re.compile(r"card-body|body|content|text", re.I)) or card

    for p in body.find_all("p"):
        text = p.get_text(strip=True)
        if not text or text.startswith("*") or len(text) <= 3:
            continue
        # Skip pure phone-number lines
        if re.match(r"^[\d\s\-\+\(\)]+$", text):
            continue
        return text

    # Fallback: look for any text block with location-like content
    for tag in body.find_all(["span", "div", "small"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 10 and not re.match(r"^[\d\s\-\+]+$", text):
            return text

    return ""


# ---------------------------------------------------------------------------
# Step 3c: Contact
# ---------------------------------------------------------------------------

def extract_contact(card: Tag) -> str:
    """Extract 10-digit Indian mobile number from card text."""
    card_text = card.get_text()
    match = re.search(r"[6-9]\d{9}", card_text)
    return match.group(0) if match else ""


# ---------------------------------------------------------------------------
# Step 3d: Find stock table
# ---------------------------------------------------------------------------

def find_stock_table(card: Tag) -> Optional[Tag]:
    """
    Find the fertilizer stock table within a dealer card.
    A valid stock table has ≥2 rows, with at least one data row containing numbers.
    """
    tables = card.find_all("table")

    if not tables:
        return None

    if len(tables) == 1:
        return tables[0]

    # Multiple tables — pick the one with numeric data rows
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        data_rows = rows[1:]
        for row in data_rows:
            cells = row.find_all(["td", "th"])
            if any(_is_numeric_text(c.get_text(strip=True)) for c in cells):
                return table

    # Fallback: largest table
    return max(tables, key=lambda t: len(t.find_all("tr")))


# ---------------------------------------------------------------------------
# Step 3e: Row classification
# ---------------------------------------------------------------------------

def _is_numeric_text(text: str) -> bool:
    """
    True if text represents a number.
    Handles: '1650', '1,650', '1650.5', '0'.
    Uses float() instead of isdigit() to handle decimals correctly.
    """
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return False
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def classify_rows(table: Tag) -> dict:
    """
    Classify rows by cell-majority content (header vs value vs other).

    Fix vs original: uses cell-majority test, not character-level isdigit(),
    so header rows with embedded codes like '(999210)' are not misclassified.
    """
    result: dict[str, list] = {
        "header_rows": [],
        "value_rows": [],
        "other_rows": [],
    }

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


# ---------------------------------------------------------------------------
# Step 3f: Validation
# ---------------------------------------------------------------------------

def validate_and_align(
    headers: list[str], values: list[str]
) -> tuple[list[str], list[str]]:
    """
    Two-tier validation:
    - FAIL (ParseError): zero headers, zero values, or no numeric values
    - WARN (truncate):   length mismatch between headers and values
    """
    if not headers:
        raise ParseError("Empty headers — not a valid stock table")
    if not values:
        raise ParseError("Empty values — table has headers but no data row")

    has_number = any(_is_numeric_text(v) for v in values)
    if not has_number:
        raise ParseError(
            f"No numeric values in data row: {values} — probably not a stock table"
        )

    if len(headers) != len(values):
        min_len = min(len(headers), len(values))
        log.warning(
            f"Header/value mismatch ({len(headers)} headers vs {len(values)} values). "
            f"Truncating to {min_len}. "
            f"Dropped: headers={headers[min_len:]}, values={values[min_len:]}"
        )
        headers = headers[:min_len]
        values = values[:min_len]

    return headers, values


# ---------------------------------------------------------------------------
# Step 3g: Header extraction + stock mapping
# ---------------------------------------------------------------------------

def extract_column_headers(classified: dict) -> list[str]:
    """
    Extract column header names from classified rows.
    When multiple header rows exist, takes the LAST (most specific) one.

    Fix vs original: avoids joining rows with '|' which creates unmappable keys.
    """
    header_rows = classified.get("header_rows", [])
    if not header_rows:
        return []

    last_row = header_rows[-1]
    cells = last_row.find_all(["td", "th"])
    return [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]


def map_stock_data(headers: list[str], raw_values: list[str]) -> dict[str, float]:
    """Map fertilizer header names → quantities. Text stored as-is (no translation)."""
    return {h.strip(): safe_parse_number(v) for h, v in zip(headers, raw_values)}


def safe_parse_number(text: str) -> float:
    """
    Robustly parse a stock quantity.
    Handles: '1,650' → 1650.0 | '' → 0.0 | '-' → 0.0 | '1650.5' → 1650.5
    """
    if not text:
        return 0.0

    text = text.strip()
    if text in ("", "-", "--", "N/A", "nil", "Nil", "NIL", "*"):
        return 0.0

    text = text.replace(",", "").replace(" ", "")
    try:
        return float(text)
    except ValueError:
        log.warning(f"Could not parse number from '{text}' — defaulting to 0.0")
        return 0.0


# ---------------------------------------------------------------------------
# Step 3h: Structure hashing
# ---------------------------------------------------------------------------

def compute_structure_signature(headers: list[str], num_value_rows: int) -> str:
    """MD5 fingerprint of table structure for site-change detection."""
    sig_input = "|".join(sorted(headers)) + f"|rows={num_value_rows}"
    return hashlib.md5(sig_input.encode("utf-8")).hexdigest()


def _check_signature(sig: str, headers: list[str]) -> None:
    """Warn if an unrecognised table structure appears."""
    if _KNOWN_SIGNATURES and sig not in _KNOWN_SIGNATURES:
        log.warning(
            f"NEW TABLE STRUCTURE — sig={sig}, headers={headers}. "
            "Parser may need updating."
        )
    _KNOWN_SIGNATURES.add(sig)


# ---------------------------------------------------------------------------
# Error snapshot helper
# ---------------------------------------------------------------------------

def _save_snapshot(html_fragment: str, district: str, block: str, error: str) -> None:
    """Save failed card HTML to logs/failed_cards/ for offline debugging."""
    try:
        os.makedirs("logs/failed_cards", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"logs/failed_cards/{district}_{block}_{ts}.html"
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(f"<!-- ERROR: {error} -->\n")
            fh.write(html_fragment)
        log.debug(f"Saved failed snapshot to {filename}")
    except Exception as exc:
        log.warning(f"Could not save snapshot: {exc}")
