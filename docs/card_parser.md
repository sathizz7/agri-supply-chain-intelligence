# 🧱 Revised Card Parser — High-Level Logic

> **Scope**: Extract dealer data from HTML cards as-is (no language translation)  
> **Resolves**: All accepted issues from [parser critique](file:///C:/Users/FAI-Sathish/.gemini/antigravity/brain/bb5e4e6f-280b-4513-9d5e-7e9c35475f8d/parser_critique.md)

---

## What Changed vs Original `parser_logic.md`

| # | Issue Fixed | What Was Wrong | What's Changed |
|---|---|---|---|
| **N7** | Card selector discovery | Completely missing — "FIND containers" was hand-waved | Multi-strategy selector chain with fallback |
| **N1** | Row classification heuristic | `any(char.isdigit())` misclassifies headers containing dealer codes `(999210)` | Cell-majority numeric test instead of character-level test |
| **N2** | Numeric validation | `isdigit()` fails on decimals `'1650.5'` and zero-stock `'0'` | `float()` try/except based validation |
| **N4** | Multi-header join | `" \| ".join()` creates unmappable compound strings | Take the most-specific (bottom) header row |
| **N5** | Validation strictness | Strict raise + card isolation = silent data loss on minor anomalies | Two-tier: WARN on mismatch (truncate), FAIL only on empty |
| **N6** | Empty results page | No detection of "zero dealers" vs "selector broke" | Explicit empty-page content sniffing |
| — | Tamil→English mapping | _Not needed_ — text extracted as-is from cards | Removed from flow |

---

## Revised Parser Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CARD PARSER PIPELINE                            │
│                                                                     │
│  INPUT: Raw HTML string from POST response                         │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ STEP 1: PAGE-LEVEL TRIAGE                                     │  │
│  │                                                               │  │
│  │  Is this a valid results page?                                │  │
│  │  ├─ YES → proceed to Step 2                                   │  │
│  │  ├─ EMPTY (legitimate) → return []                            │  │
│  │  └─ ERROR/UNKNOWN → log + save snapshot + return []           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ STEP 2: CARD DISCOVERY                                        │  │
│  │                                                               │  │
│  │  Find all dealer card containers using selector chain:        │  │
│  │  Try selector 1 → Try selector 2 → ... → Fallback            │  │
│  │                                                               │  │
│  │  Result: List of card HTML elements                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ STEP 3: PER-CARD PARSING (isolated)                           │  │
│  │                                                               │  │
│  │  FOR each card:                                               │  │
│  │    TRY:                                                       │  │
│  │      3a. Extract dealer identity (name, code)                 │  │
│  │      3b. Extract address                                      │  │
│  │      3c. Extract contact (phone)                              │  │
│  │      3d. Find the stock table inside card                     │  │
│  │      3e. Classify rows dynamically (header vs value)          │  │
│  │      3f. Validate structure (two-tier)                        │  │
│  │      3g. Map headers to values (index-locked)                 │  │
│  │      3h. Hash structure signature                             │  │
│  │      → Append to results                                      │  │
│  │    EXCEPT:                                                    │  │
│  │      → log error + save raw snapshot + continue               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  OUTPUT: List[DealerRecord]                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Page-Level Triage

**Why this exists**: Before parsing cards, we must confirm the page is a valid results page. The POST response might be an error page, a session-expired redirect, or a legitimate "no dealers in this block" message.

```python
def triage_page(soup: BeautifulSoup) -> str:
    """
    Classify the page before attempting card parsing.

    Returns:
        'HAS_RESULTS'  — Page contains dealer cards, proceed with parsing
        'EMPTY'        — No dealers in this block (legitimate zero-result)
        'ERROR'        — Page is an error/redirect/unexpected content
    """
    page_text = soup.get_text(separator=' ', strip=True)

    # --- Check for known "no data" messages (Tamil) ---
    NO_DATA_MARKERS = [
        'தகவல் இல்லை',       # "No information"
        'முடிவுகள் இல்லை',    # "No results"
        'தரவு இல்லை',        # "No data"
    ]
    if any(marker in page_text for marker in NO_DATA_MARKERS):
        return 'EMPTY'

    # --- Check for session/error indicators ---
    ERROR_MARKERS = [
        'login', 'session expired', 'unauthorized',
        '500', '404', 'error',
    ]
    if any(marker in page_text.lower() for marker in ERROR_MARKERS):
        return 'ERROR'

    # --- Check if page has any table-containing containers ---
    if soup.find('table'):
        return 'HAS_RESULTS'

    # --- Page has content but no tables — uncertain ---
    if len(page_text) > 100:
        return 'ERROR'   # has content but no tables = probably wrong page

    return 'EMPTY'       # very little content = likely empty result
```

**Reasoning**: Without this step, a session-expired login page would silently produce zero records, and you'd never know the scrape failed. Page triage catches this immediately.

---

## Step 2: Card Discovery (Selector Chain)

**Why this was the #1 critical fix**: The original parser said "FIND all dealer containers" without specifying _how_. This is the hardest part — CSS selectors change when the website is updated. A chain of selectors with fallback makes the parser resilient.

```python
# Ordered from most-specific to least-specific.
# The first selector that returns results wins.
CARD_SELECTORS = [
    # --- PRIMARY: Discovered during reconnaissance ---
    # These are the exact selectors observed on the live site.
    # Update these after running recon/save_samples.py
    {
        'tag': 'div',
        'attrs': {'class': 'card'},
        'label': 'Bootstrap card',
    },
    {
        'tag': 'div',
        'attrs': {'class': 'dealer-card'},
        'label': 'Custom dealer card',
    },
    {
        'tag': 'div',
        'attrs': {'class': 'panel'},
        'label': 'Bootstrap panel',
    },

    # --- FALLBACK: Structural heuristic ---
    # Any <div> that directly contains both a header-like element AND a <table>
    # is likely a dealer card.
    None,  # Sentinel — triggers fallback logic
]


def discover_cards(soup: BeautifulSoup) -> list:
    """
    Find all dealer card containers using a prioritized selector chain.
    Falls back to structural heuristic if no named selector matches.

    Returns:
        List of BeautifulSoup Tag elements, each representing one dealer card.
    """
    for selector in CARD_SELECTORS:
        if selector is None:
            # --- FALLBACK: find any div containing a <table> ---
            cards = [
                div for div in soup.find_all('div')
                if div.find('table')
                and not div.find('div', recursive=False)  # avoid parent wrappers
                   or len(div.find_all('table')) == 1      # exactly 1 table inside
            ]
            if cards:
                log.info(f"Card discovery: using FALLBACK heuristic, found {len(cards)}")
                return cards
        else:
            cards = soup.find_all(selector['tag'], attrs=selector['attrs'])
            if cards:
                log.info(
                    f"Card discovery: matched '{selector['label']}', "
                    f"found {len(cards)} cards"
                )
                return cards

    log.warning("Card discovery: NO selectors matched. Page may have changed.")
    return []
```

**Reasoning**: Government websites use whatever CSS framework was current when the site was built. If they migrate from Bootstrap 3 (panels) to Bootstrap 5 (cards), the primary selector fails but the fallback catches it. The pipeline logs _which_ selector matched so you know when to update.

---

## Step 3a: Extract Dealer Identity

**Why this was changed**: The original didn't define how to separate dealer name from dealer code. The code (e.g., `999210`) is inside parentheses in the card header.

```python
import re

def extract_dealer_identity(card) -> dict:
    """
    Extract dealer name and code from card header.

    Expected format: "தத்தூர் வேளாண்மை கடன் சங்கம் (999210)"
    
    Returns: {'name': 'தத்தூர் வேளாண்மை கடன் சங்கம்', 'code': '999210'}
    """
    # Strategy: search multiple possible header locations
    HEADER_SELECTORS = [
        lambda c: c.find(class_=re.compile(r'card-header|header|title', re.I)),
        lambda c: c.find(['h3', 'h4', 'h5', 'strong', 'b']),
        lambda c: c,  # last resort: search entire card text
    ]

    for selector_fn in HEADER_SELECTORS:
        element = selector_fn(card)
        if element:
            text = element.get_text(strip=True)
            if text and len(text) > 3:
                break
    else:
        return {'name': '', 'code': ''}

    # --- Extract code from parentheses ---
    code_match = re.search(r'\((\d{4,})\)', text)
    if code_match:
        code = code_match.group(1)
        name = text[:code_match.start()].strip()
    else:
        code = ''
        name = text.strip()

    return {'name': name, 'code': code}
```

**Reasoning**: The regex `\((\d{4,})\)` specifically looks for 4+ digit numbers in parentheses — this avoids matching short numbers that might appear in addresses or other text. Multiple header selectors ensure we find the name regardless of which HTML tag the site uses.

---

## Step 3b–3c: Extract Address & Contact

```python
def extract_address(card) -> str:
    """
    Extract dealer address from card body.
    Typically the first <p> or text block after the header.
    """
    # Skip header, find first paragraph-like element
    body = card.find(class_=re.compile(r'card-body|body|content', re.I))
    if not body:
        body = card

    # First <p> tag that isn't a footer/note
    for p in body.find_all('p'):
        text = p.get_text(strip=True)
        # Skip unit notes like "* அளவு கிலோவில்"
        if text and not text.startswith('*') and len(text) > 3:
            # Skip if it looks like a phone number
            if not re.match(r'^[\d\s\-\+]+$', text):
                return text

    return ''


def extract_contact(card) -> str:
    """
    Extract 10-digit Indian mobile number from card.
    Searches the entire card text for a phone pattern.
    """
    card_text = card.get_text()

    # Indian mobile: starts with 6-9, exactly 10 digits
    match = re.search(r'[6-9]\d{9}', card_text)
    return match.group(0) if match else ''
```

---

## Step 3d: Find Stock Table Inside Card

```python
def find_stock_table(card) -> 'Tag | None':
    """
    Locate the fertilizer stock table embedded within a dealer card.
    
    A valid stock table has:
    - At least 2 rows (header + data)
    - Header row with non-numeric text (fertilizer names)
    - Data row with mostly numeric values
    """
    tables = card.find_all('table')

    if len(tables) == 0:
        return None

    if len(tables) == 1:
        return tables[0]

    # Multiple tables in card — pick the one that looks like stock data
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) >= 2:
            # Check if second row has numeric content
            second_row_cells = rows[1].find_all('td')
            numeric_cells = sum(
                1 for c in second_row_cells
                if _is_numeric_text(c.get_text(strip=True))
            )
            if numeric_cells > 0:
                return table

    # Fallback: return the largest table
    return max(tables, key=lambda t: len(t.find_all('tr')))
```

---

## Step 3e: Dynamic Row Classification (FIXED)

**What was wrong**: The original used `any(char.isdigit() for char in text)` which misclassifies header rows that contain dealer codes like `(999210)`.

**Fix**: Check if the _majority of cells_ in a row are numeric, not just any character in the entire row text.

```python
def _is_numeric_text(text: str) -> bool:
    """
    Check if a text string represents a number.
    Uses float() conversion instead of isdigit() to handle decimals and commas.
    
    '1650'   → True
    '1,650'  → True
    '0'      → True
    '1650.5' → True
    'டி ஏ பி'→ False
    ''       → False (empty is not numeric)
    """
    cleaned = text.strip().replace(',', '')
    if not cleaned:
        return False
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def classify_rows(table) -> dict:
    """
    Dynamically classify table rows by their CONTENT, not position.

    Returns: {
        'header_rows': [row, ...],   # Rows where majority of cells are text
        'value_rows':  [row, ...],   # Rows where majority of cells are numeric
        'other_rows':  [row, ...],   # Footer, notes, etc.
    }

    REASONING for the fix:
    The original used `any(char.isdigit() for char in row.get_text())`
    which breaks because:
      - Header row "தத்தூர் (999210)" contains digits → misclassified as value
      - "0" is numeric but `isdigit()` on individual chars works inconsistently
    
    The fix checks CELL-LEVEL majority:
      - A row with 5 cells, 4 of which are numbers → value row
      - A row with 5 cells, 4 of which are text   → header row
    """
    classified = {
        'header_rows': [],
        'value_rows': [],
        'other_rows': [],
    }

    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue

        cell_texts = [c.get_text(strip=True) for c in cells]

        # Skip rows with only empty cells
        if all(not t for t in cell_texts):
            continue

        non_empty = [t for t in cell_texts if t]
        if not non_empty:
            continue

        # Count how many cells are numeric
        numeric_count = sum(1 for t in non_empty if _is_numeric_text(t))
        numeric_ratio = numeric_count / len(non_empty)

        if numeric_ratio > 0.5:
            # Majority numeric → this is a value/data row
            classified['value_rows'].append(row)
        elif numeric_ratio == 0:
            # Fully non-numeric → header row
            classified['header_rows'].append(row)
        else:
            # Mixed — could be a total row or note
            classified['other_rows'].append(row)

    return classified
```

**Why cell-majority works**:

| Row Content | Cells | Numeric Cells | Ratio | Classification |
|---|---|---|---|---|
| `யூரியா \| டி ஏ பி \| பொட்டாஸ்` | 3 | 0 | 0.0 | ✅ header |
| `1650 \| 500 \| 0` | 3 | 3 | 1.0 | ✅ value |
| `தத்தூர் சங்கம் (999210)` | 1 | 0 | 0.0 | ✅ header (text with embedded digits, but cell itself isn't purely numeric) |
| `Total \| 2150` | 2 | 1 | 0.5 | → other (mixed) |

---

## Step 3f: Two-Tier Validation (FIXED)

**What was wrong**: The original raised `StructuralError` on any mismatch, and card-level isolation silently dropped the entire dealer. Minor anomalies (extra column, trailing empty cell) caused silent data loss.

**Fix**: Two tiers — WARN and truncate on mismatch, FAIL only on truly broken structure.

```python
class ParseWarning(Exception):
    """Non-fatal: data was recovered with adjustments."""
    pass

class ParseError(Exception):
    """Fatal: card cannot be parsed at all."""
    pass


def validate_and_align(headers: list[str], values: list[str]) -> tuple[list, list]:
    """
    Two-tier validation:
    
    TIER 1 (FATAL → raise ParseError):
        - Zero headers
        - Zero values  
        - No numeric values at all (probably not a stock table)
    
    TIER 2 (WARNING → truncate and continue):
        - Header/value length mismatch (truncate to shorter)
    
    Returns:
        Aligned (headers, values) of equal length.
    
    REASONING:
        The original raised StructuralError on ANY mismatch.
        Combined with card-level isolation, this silently dropped dealers
        whenever the site added even one extra column.
        
        Now:
        - Extra <td> at the end?       → WARN, truncate, keep the data
        - Completely empty table?       → FAIL, save snapshot for debugging
    """
    # --- TIER 1: Fatal checks ---
    if len(headers) == 0:
        raise ParseError("Empty headers — not a valid stock table")

    if len(values) == 0:
        raise ParseError("Empty values — table has headers but no data row")

    # Check for at least one numeric value
    has_number = any(_is_numeric_text(v) for v in values)
    if not has_number:
        raise ParseError(
            f"No numeric values found in data row: {values} "
            f"— probably not a stock table"
        )

    # --- TIER 2: Soft alignment ---
    if len(headers) != len(values):
        min_len = min(len(headers), len(values))
        log.warning(
            f"Header/value mismatch ({len(headers)} headers, {len(values)} values). "
            f"Truncating to {min_len} columns. "
            f"Dropped headers: {headers[min_len:]} | Dropped values: {values[min_len:]}"
        )
        headers = headers[:min_len]
        values = values[:min_len]

    return headers, values
```

---

## Step 3g: Header Extraction (Multi-Row Safe) (FIXED)

**What was wrong**: The original joined multiple header rows with `" | "`, creating compound strings like `"வகை | டி ஏ பி"` that are useless as column names.

**Fix**: When there are multiple header rows, take the **bottom-most** (most specific) row as the column names. The top rows are usually category labels.

```python
def extract_column_headers(classified_rows: dict) -> list[str]:
    """
    Extract clean column header names from classified header rows.

    Strategy:
    - If 1 header row:  use it directly
    - If 2+ header rows: use the LAST (most specific) row
    
    Example:
        Header row 1: "வகை"  |  "வகை"   |  "வகை"      ← category ("Type")
        Header row 2: "யூரியா" | "டி ஏ பி" | "பொட்டாஸ்"  ← specific names
        
        → Returns: ["யூரியா", "டி ஏ பி", "பொட்டாஸ்"]  (bottom row wins)

    REASONING:
        The original joined them: "வகை | யூரியா" — unusable as a key.
        The bottom row is always the specific fertilizer name.
        The top row is a grouping label that adds no value.
    """
    header_rows = classified_rows.get('header_rows', [])

    if not header_rows:
        return []

    # Use the LAST header row (most specific)
    last_row = header_rows[-1]
    cells = last_row.find_all(['td', 'th'])

    headers = [cell.get_text(strip=True) for cell in cells]

    # Filter out empty headers
    return [h for h in headers if h]
```

---

## Step 3g (continued): Index-Locked Mapping

**Retained from original** — maps headers to values by index, but stores them as-is (no translation).

```python
def map_stock_data(headers: list[str], values: list[str]) -> dict:
    """
    Map fertilizer headers to their stock values using strict index alignment.
    
    Text is stored AS-IS from the card (no Tamil→English conversion).
    
    Returns: {
        'யூரியா': 1650.0,
        'டி ஏ பி': 500.0,
        'பொட்டாஸ்': 0.0,
    }
    """
    stock_data = {}

    for i in range(len(headers)):
        header = headers[i].strip()
        raw_value = values[i].strip()
        
        # Parse numeric value safely
        quantity = safe_parse_number(raw_value)
        stock_data[header] = quantity

    return stock_data
```

---

## Step 3h: Structure Hashing

**Retained from original** — production-grade site-change detection.

```python
import hashlib


def compute_structure_signature(headers: list[str], num_value_rows: int) -> str:
    """
    Generate a fingerprint of the table structure.
    Stored per scrape run — if it changes between runs, the website has been updated.
    
    Signature components:
        - Sorted header names (order-independent)
        - Number of value rows
        
    Returns: hex digest string
    """
    signature_input = "|".join(sorted(headers)) + f"|rows={num_value_rows}"
    return hashlib.md5(signature_input.encode('utf-8')).hexdigest()


# Known valid signatures — populated during first successful scrape
KNOWN_SIGNATURES = set()

def check_signature(sig: str, headers: list[str]):
    """Alert if an unknown structure is detected."""
    if KNOWN_SIGNATURES and sig not in KNOWN_SIGNATURES:
        log.warning(
            f"⚠️ NEW TABLE STRUCTURE DETECTED — signature: {sig}, "
            f"headers: {headers}. "
            f"Parser may need updating."
        )
```

---

## Step 3 (except): Error Handling + Raw Snapshot

**Retained from original** — card-level isolation with raw HTML capture for offline debugging.

```python
import os
from datetime import datetime


def save_failed_card(card_html: str, district: str, block: str, error: str):
    """
    Save the raw HTML of a card that failed to parse.
    Stored in logs/failed_cards/ for offline debugging.
    """
    os.makedirs('logs/failed_cards', exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"logs/failed_cards/{district}_{block}_{timestamp}.html"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"<!-- ERROR: {error} -->\n")
        f.write(card_html)

    log.info(f"Saved failed card to {filename}")
```

---

## Strict Numeric Parsing (FIXED)

**What was wrong**: `isdigit()` fails on `'1650.5'` and `'0.0'`. Bare `except:` catches all exceptions silently.

```python
def safe_parse_number(text: str) -> float:
    """
    Robustly parse a stock quantity from HTML text.

    Handles: '1,650' → 1650.0
             '0'     → 0.0
             ''      → 0.0
             'N/A'   → 0.0
             '-'     → 0.0
             '1650.5'→ 1650.5
    
    REASONING for the fix:
        Original used isdigit() which fails on '1650.5' (decimal point).
        Original bare `except:` hid real bugs.
        Now uses explicit float() with specific ValueError catch.
    """
    if not text:
        return 0.0

    text = text.strip()

    # Known non-numeric tokens
    if text in ('', '-', '--', 'N/A', 'nil', 'Nil', 'NIL', '*'):
        return 0.0

    # Remove commas and whitespace
    text = text.replace(',', '').replace(' ', '')

    try:
        return float(text)
    except ValueError:
        log.warning(f"Could not parse number from: '{text}' — defaulting to 0.0")
        return 0.0
```

---

## Complete Flow — Putting It All Together

```python
def parse_results_page(html: str, district: dict, block: dict) -> list[dict]:
    """
    MASTER ENTRY POINT
    
    Takes raw HTML from POST response.
    Returns list of structured dealer records.
    """
    soup = BeautifulSoup(html, 'lxml')

    # ── STEP 1: Page Triage ──
    page_status = triage_page(soup)

    if page_status == 'EMPTY':
        log.info(f"No dealers in {district['name_ta']} > {block['name_ta']}")
        return []

    if page_status == 'ERROR':
        log.error(f"Error page received for {district['name_ta']} > {block['name_ta']}")
        save_failed_card(str(soup)[:5000], district.get('code',''), block.get('code',''), 'ERROR_PAGE')
        return []

    # ── STEP 2: Discover Cards ──
    cards = discover_cards(soup)

    if not cards:
        log.warning(
            f"No cards found in {district['name_ta']} > {block['name_ta']} "
            f"despite HAS_RESULTS triage — selector may need updating"
        )
        save_failed_card(str(soup)[:5000], district.get('code',''), block.get('code',''), 'NO_CARDS_FOUND')
        return []

    # ── STEP 3: Parse Each Card (Isolated) ──
    results = []

    for card in cards:
        try:
            # 3a. Dealer identity
            identity = extract_dealer_identity(card)
            if not identity['name']:
                continue  # skip non-dealer elements

            # 3b. Address
            address = extract_address(card)

            # 3c. Contact
            contact = extract_contact(card)

            # 3d. Find stock table
            table = find_stock_table(card)
            stocks = {}
            structure_sig = None

            if table:
                # 3e. Classify rows
                classified = classify_rows(table)

                # 3f+3g. Extract and align headers/values
                headers = extract_column_headers(classified)

                value_rows = classified.get('value_rows', [])
                if value_rows and headers:
                    # Take first value row (usually the only one)
                    first_value_row = value_rows[0]
                    values = [
                        td.get_text(strip=True)
                        for td in first_value_row.find_all('td')
                    ]

                    # Validate and align
                    headers, values = validate_and_align(headers, values)

                    # Map to dict
                    stocks = map_stock_data(headers, values)

                    # 3h. Structure hash
                    structure_sig = compute_structure_signature(
                        headers, len(value_rows)
                    )
                    check_signature(structure_sig, headers)

            # ── Build record ──
            record = {
                'dealer_name':   identity['name'],
                'dealer_code':   identity['code'],
                'address':       address,
                'contact':       contact,
                'district_code': district['code'],
                'district_name': district['name_ta'],
                'block_code':    block['code'],
                'block_name':    block['name_ta'],
                'stocks':        stocks,
                'structure_sig': structure_sig,
            }
            results.append(record)

        except ParseError as e:
            # Fatal card error — save and continue
            log.error(f"Card parse FAILED: {e}")
            save_failed_card(str(card), district.get('code',''), block.get('code',''), str(e))
            continue

        except Exception as e:
            # Unexpected error — save and continue
            log.error(f"Unexpected card error: {e}", exc_info=True)
            save_failed_card(str(card), district.get('code',''), block.get('code',''), str(e))
            continue

    log.info(
        f"Parsed {len(results)}/{len(cards)} cards "
        f"in {district['name_ta']} > {block['name_ta']}"
    )
    return results
```

---

## Output Schema

Each parsed dealer record:

```python
{
    'dealer_name':   'தத்தூர் வேளாண்மை கூட்டுறவு கடன் சங்கம்',  # as-is from card
    'dealer_code':   '999210',                                    # from parentheses
    'address':       'தத்தூர், ஆண்டிமடம்',                       # as-is
    'contact':       '9841713690',                                # 10-digit extracted
    'district_code': '1',
    'district_name': 'அரியலூர்',                                 # as-is from dropdown
    'block_code':    '101',
    'block_name':    'ஆண்டிமடம்',                                # as-is from dropdown
    'stocks': {
        'யூரியா':    1650.0,     # header text as-is → parsed numeric value
        'டி ஏ பி':   500.0,
        'பொட்டாஸ்':  0.0,
    },
    'structure_sig': 'a1b2c3d4e5f6...',   # MD5 of table structure
}
```

---

## Summary of Fixes Applied

| Fix | Before (Broken) | After (Fixed) | Reasoning |
|---|---|---|---|
| Card discovery | "FIND containers" (unspecified) | Ordered selector chain with structural fallback | Most critical — without this, nothing works |
| Row classifier | `any(char.isdigit() for char in row_text)` | Cell-majority numeric test (`numeric_count/total > 0.5`) | Header `(999210)` was misclassified as value row |
| Numeric validation | `v.strip().replace(',','').isdigit()` | `float()` try/except | `isdigit()` fails on `'0.5'`, `'1,650.5'` |
| Multi-header | `" \| ".join(parts)` across rows | Use bottom-most header row | Join created unmappable compound strings |
| Validation strictness | Single `raise StructuralError` | Two-tier: WARN+truncate vs FAIL | Extra column silently dropped entire dealer |
| Empty page | Not handled | `triage_page()` with Tamil "no data" markers | Zero results vs broken selector was indistinguishable |
| Text storage | Tamil→English conversion | As-is extraction | Per user requirement — no translation layer |
