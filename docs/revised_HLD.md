# 🌾 TFAIS — Revised High-Level Design (HLD)

**Tamil Nadu Fertilizer Availability Intelligence System**

> This document supersedes `intial_LLD.md`. It incorporates all findings from the [senior review](file:///C:/Users/FAI-Sathish/.gemini/antigravity/brain/bb5e4e6f-280b-4513-9d5e-7e9c35475f8d/lld_review.md) conducted after live inspection of the target website.

---

## 1. Problem Recap

The Tamil Nadu government fertilizer portal exposes district→block→dealer stock data via an interactive web form. The data is:

- **Not machine-readable** — no public API, no CSV exports
- **POST-driven** — requires form submissions, not URL crawling
- **Tamil-language** — all labels, names, and fertilizer types in Tamil
- **Card-based** — results are rendered as dealer cards, not flat tables

Our goal: build a reliable scraper pipeline to extract, normalize, and store this data daily for a dashboard.

---

## 2. What Changed From the Original LLD (and Why)

| # | Original Assumption | Reality (from live inspection) | Impact |
|---|---|---|---|
| 1 | GET-based URL drill-down `/tm/{dist}/{block}/` | POST-based form submission to `/Fertilizer/result/tm` | Entire scraping strategy redesigned |
| 2 | Single flat `<table>` with dealer rows | Card-based grid, each dealer = separate card with inner mini-table | Parser completely rewritten |
| 3 | Fixed column indices `cols[3]=Urea` | Dynamic columns per dealer, headers in Tamil | Header-driven parsing + Tamil→English map |
| 4 | Stateless HTTP GETs | Session-dependent form workflow (cookies, possible CSRF) | `requests.Session()` required |
| 5 | `requests` + `BeautifulSoup` sufficient | AngularJS + jQuery dynamic page, AJAX-populated dropdowns | Need Playwright fallback strategy |
| 6 | `fertilizer_name` as free VARCHAR | Inconsistent naming risk over time | Added `fertilizers` master table |
| 7 | `UNIQUE(license_no)` for dealer dedup | License numbers not visible in card layout | Changed to `UNIQUE(dealer_code, block_id)` |
| 8 | Sequential scraping only | ~570 requests × 2s = 19 min minimum | Added async concurrency option |
| 9 | Single try/except for entire pipeline | One failure kills entire run | Per-district error isolation |
| 10 | Checkpointing mentioned but undesigned | No resume capability on failure | Designed checkpoint table |

---

## 3. Revised System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TFAIS SCRAPER PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│   │  PHASE 0     │    │  PHASE 1     │    │  PHASE 2     │             │
│   │  Recon &     │───▶│  Scraper     │───▶│  Card        │             │
│   │  Session     │    │  (POST-based)│    │  Parser      │             │
│   │  Bootstrap   │    │              │    │              │             │
│   └──────────────┘    └──────────────┘    └──────┬───────┘             │
│                                                   │                     │
│                                                   ▼                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│   │  PHASE 5     │    │  PHASE 4     │    │  PHASE 3     │             │
│   │  Scheduler   │◀───│  Checkpoint  │◀───│  Normalizer  │             │
│   │  (daily run) │    │  + Recovery  │    │  + DB Store  │             │
│   └──────────────┘    └──────────────┘    └──────────────┘             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Phase-by-Phase Design

### Phase 0: Reconnaissance & Session Bootstrap

**Priority**: 🔴 CRITICAL — Must be completed first

**Purpose**: Establish an HTTP session and extract the full list of district IDs and names from the form dropdowns. This replaces the old "URL pattern discovery" approach.

**How it works**:

```
┌──────────────────────────────────────┐
│  GET  /fertilizer/stock/tm/20/2020   │
│                                      │
│  Returns HTML with:                  │
│  ┌────────────────────────────────┐  │
│  │ <select id="district">         │  │
│  │   <option value="1">அரியலூர்  │  │
│  │   <option value="2">செங்கல்...│  │
│  │   ...38 districts              │  │
│  └────────────────────────────────┘  │
│                                      │
│  Also captures:                      │
│  • Session cookies                   │
│  • CSRF token (if present)           │
│  • Any hidden form fields            │
└──────────────────────────────────────┘
```

**Implementation** — `scraper/session_manager.py`:

```python
import requests
from bs4 import BeautifulSoup

class SessionManager:
    """
    Manages a persistent HTTP session for the entire scrape run.
    Handles cookies, CSRF tokens, and form metadata automatically.
    """
    BASE_URL = "http://115.243.209.84/people_app"
    ENTRY_URL = f"{BASE_URL}/fertilizer/stock/tm/20/2020"
    BLOCKS_URL = f"{BASE_URL}/Fertilizer/getBlocks"    # + /{district_id}
    RESULTS_URL = f"{BASE_URL}/Fertilizer/result/tm"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ta;q=0.8',
        })
        self._csrf_token = None
        self._hidden_fields = {}

    def bootstrap(self) -> list[dict]:
        """
        GET the entry page, establish session, extract district list.
        Returns: [{'code': '1', 'name_ta': 'அரியலூர்'}, ...]
        """
        resp = self.session.get(self.ENTRY_URL, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'lxml')

        # Extract CSRF token if present
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input:
            self._csrf_token = csrf_input['value']

        # Extract hidden form fields
        for hidden in soup.find_all('input', {'type': 'hidden'}):
            self._hidden_fields[hidden.get('name', '')] = hidden.get('value', '')

        # Extract districts from <select> dropdown
        districts = []
        select = soup.find('select', {'id': lambda x: x and 'district' in x.lower()})
        if select:
            for option in select.find_all('option'):
                val = option.get('value', '').strip()
                if val and val != '0':  # skip "Select District" placeholder
                    districts.append({
                        'code': val,
                        'name_ta': option.get_text(strip=True)
                    })

        return districts

    def get_blocks_for_district(self, district_code: str) -> list[dict]:
        """
        POST to /getBlocks/{district_id} to fetch blocks.
        Returns: [{'code': '101', 'name_ta': 'ஆண்டிமடம்'}, ...]
        """
        url = f"{self.BLOCKS_URL}/{district_code}"
        resp = self.session.post(url, timeout=30)
        resp.raise_for_status()

        # Response may be JSON or HTML - handle both
        try:
            data = resp.json()
            # If JSON: parse as list of {id, name} objects
            return [{'code': str(b['id']), 'name_ta': b['name']} for b in data]
        except ValueError:
            # If HTML: parse as <option> tags
            soup = BeautifulSoup(resp.text, 'lxml')
            blocks = []
            for option in soup.find_all('option'):
                val = option.get('value', '').strip()
                if val and val != '0':
                    blocks.append({
                        'code': val,
                        'name_ta': option.get_text(strip=True)
                    })
            return blocks

    def fetch_results(self, district_code: str, block_code: str) -> str:
        """
        POST the search form to get dealer stock results HTML.
        Returns: Raw HTML string of the results page.
        """
        form_data = {
            'district': district_code,
            'block': block_code,
            **self._hidden_fields,
        }
        if self._csrf_token:
            form_data['_token'] = self._csrf_token

        resp = self.session.post(self.RESULTS_URL, data=form_data, timeout=30)
        resp.raise_for_status()
        return resp.text
```

**Key design decisions**:
- Single `requests.Session()` object reused across all requests (cookies persist)
- CSRF token extracted once and reused (re-extracted if it expires)
- `getBlocks` response handled as both JSON and HTML (defensive parsing)

---

### Phase 1: POST-Based Scraper

**Priority**: 🔴 CRITICAL — Replaces the entire old scraping strategy

**Purpose**: Systematically iterate over all (district, block) pairs using the session manager. This replaces the old GET-based URL hierarchy.

**The corrected data flow**:

```
                          ┌─────────────────────────────┐
                          │    1. GET Entry Page         │
                          │    Extract district <select> │
                          │    Establish session cookies  │
                          └──────────────┬──────────────┘
                                         │
                      ┌──────────────────┼──────────────────┐
                      ▼                  ▼                  ▼
              ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
              │  District 1  │  │  District 2  │  │  District N  │
              │  POST blocks │  │  POST blocks │  │  POST blocks │
              └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                     │                 │                 │
              ┌──────┴───────┐  ┌──────┴───────┐         │
              ▼              ▼  ▼              ▼         ▼
        ┌──────────┐  ┌──────────┐  ...
        │ Block A  │  │ Block B  │
        │ POST     │  │ POST     │
        │ results  │  │ results  │
        └──────────┘  └──────────┘
              │              │
              ▼              ▼
        ┌──────────┐  ┌──────────┐
        │ Parse    │  │ Parse    │
        │ Cards    │  │ Cards    │
        └──────────┘  └──────────┘
```

**Implementation** — `scraper/scraper.py`:

```python
import time
import logging
from scraper.session_manager import SessionManager

log = logging.getLogger(__name__)

class FertilizerScraper:
    """
    Orchestrates the scraping of all district→block→dealer data
    using POST-based form submissions.
    """

    def __init__(self, session_manager: SessionManager, rate_limit: float = 2.0):
        self.sm = session_manager
        self.rate_limit = rate_limit

    def scrape_all(self) -> list[dict]:
        """
        Full scrape: all districts → all blocks → all results.
        Yields raw HTML results keyed by (district, block).
        """
        districts = self.sm.bootstrap()
        log.info(f"Found {len(districts)} districts")

        results = []

        for district in districts:
            try:
                blocks = self.sm.get_blocks_for_district(district['code'])
                log.info(f"  {district['name_ta']}: {len(blocks)} blocks")

                for block in blocks:
                    try:
                        html = self.sm.fetch_results(district['code'], block['code'])
                        results.append({
                            'district': district,
                            'block': block,
                            'html': html,
                        })
                        time.sleep(self.rate_limit)  # respectful delay

                    except Exception as e:
                        log.error(
                            f"    FAILED block {block['name_ta']} "
                            f"in {district['name_ta']}: {e}"
                        )
                        continue  # don't kill the whole run

            except Exception as e:
                log.error(f"  FAILED district {district['name_ta']}: {e}")
                continue  # isolate district failures

        return results
```

**Why this approach solves Critical Issues #1, #4, #9**:
- ✅ **POST-based** — mirrors the real form workflow
- ✅ **Session-managed** — cookies and CSRF persist
- ✅ **Error-isolated** — per-block and per-district try/except, pipeline never dies

---

### Phase 2: Card Parser

**Priority**: 🔴 CRITICAL — Replaces the flat-table parser

**Purpose**: Parse the card-based results HTML into structured Python dicts. Each card represents one dealer with an embedded stock mini-table.

**What a dealer card looks like in HTML** (observed from live site):

```html
<div class="card">
  <div class="card-header">
    தத்தூர் தொடக்க வேளாண்மை கூட்டுறவு கடன் சங்கம் (999210)
  </div>
  <div class="card-body">
    <p>தத்தூர், ஆண்டிமடம்</p>
    <table>
      <tr><th>யூரியா</th><th>டி ஏ பி</th><th>பொட்டாஸ்</th></tr>
      <tr><td>1650</td><td>500</td><td>0</td></tr>
    </table>
    <p>Mobile: 9841713690</p>
  </div>
</div>
```

> [!IMPORTANT]
> The exact CSS classes and HTML structure must be verified during Phase 0 reconnaissance by saving sample HTML files. The above is **representative**, not guaranteed.

**Implementation** — `parser/card_parser.py`:

```python
import re
from bs4 import BeautifulSoup
from parser.fertilizer_map import normalize_fertilizer_name
from parser.data_cleaner import DataCleaner

class CardParser:
    """
    Parses card-based dealer results page.
    Each card = one dealer with variable-width stock table.
    """

    def parse_results_page(self, html: str, district: dict, block: dict) -> list[dict]:
        """
        Parse a full results page into a list of dealer records.

        Returns: [{
            'dealer_name': 'XYZ Agro',
            'dealer_code': '999210',
            'address': 'தத்தூர், ஆண்டிமடம்',
            'contact': '9841713690',
            'district_code': '1',
            'district_name_ta': 'அரியலூர்',
            'block_code': '101',
            'block_name_ta': 'ஆண்டிமடம்',
            'stocks': {'Urea': 1650.0, 'DAP': 500.0, 'Potash/MOP': 0.0}
        }, ...]
        """
        soup = BeautifulSoup(html, 'lxml')
        cards = soup.find_all('div', class_=re.compile(r'card|dealer|result', re.I))

        # Fallback: if no cards found, try broader selectors
        if not cards:
            cards = soup.find_all('div', class_=True)
            cards = [c for c in cards if c.find('table')]

        results = []
        for card in cards:
            try:
                record = self._parse_single_card(card, district, block)
                if record:
                    results.append(record)
            except Exception as e:
                # Log but don't fail — some cards may be malformed
                import logging
                logging.getLogger(__name__).warning(f"Failed to parse card: {e}")
                continue

        return results

    def _parse_single_card(self, card, district: dict, block: dict) -> dict | None:
        """Parse one dealer card into a structured dict."""

        # --- Extract dealer name and code from header ---
        header = card.find(class_=re.compile(r'header|title', re.I))
        if not header:
            header = card  # fallback: search in card itself

        header_text = header.get_text(strip=True)
        dealer_name, dealer_code = self._extract_name_and_code(header_text)

        if not dealer_name:
            return None  # not a valid dealer card

        # --- Extract address ---
        address = ''
        address_el = card.find('p')
        if address_el:
            address = address_el.get_text(strip=True)

        # --- Extract contact (mobile) ---
        contact = ''
        contact_match = re.search(r'(\d{10})', card.get_text())
        if contact_match:
            contact = contact_match.group(1)

        # --- Parse the stock mini-table (DYNAMIC HEADERS) ---
        stocks = {}
        table = card.find('table')
        if table:
            stocks = self._parse_stock_table(table)

        return {
            'dealer_name': dealer_name,
            'dealer_code': dealer_code,
            'address': address,
            'contact': contact,
            'district_code': district['code'],
            'district_name_ta': district['name_ta'],
            'block_code': block['code'],
            'block_name_ta': block['name_ta'],
            'stocks': stocks,
        }

    def _extract_name_and_code(self, text: str) -> tuple[str, str]:
        """
        From: 'தத்தூர் தொடக்க வேளாண்மை (999210)'
        To:   ('தத்தூர் தொடக்க வேளாண்மை', '999210')
        """
        match = re.search(r'\((\d+)\)', text)
        if match:
            code = match.group(1)
            name = text[:match.start()].strip()
            return name, code
        return text.strip(), ''

    def _parse_stock_table(self, table) -> dict:
        """
        Parse a variable-width stock table with Tamil headers.

        Example table:
          | யூரியா | டி ஏ பி | பொட்டாஸ் |
          |  1650  |   500   |    0     |

        Returns: {'Urea': 1650.0, 'DAP': 500.0, 'Potash/MOP': 0.0}
        """
        rows = table.find_all('tr')
        if len(rows) < 2:
            return {}

        # Row 0: headers (Tamil fertilizer names)
        headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]

        # Row 1: values
        values = [td.get_text(strip=True) for td in rows[1].find_all('td')]

        stocks = {}
        for header, value in zip(headers, values):
            english_name = normalize_fertilizer_name(header)
            if english_name:
                stocks[english_name] = DataCleaner.parse_number_from_text(value)

        return stocks
```

**Implementation** — `parser/fertilizer_map.py`:

```python
"""
Tamil → English fertilizer name mapping.
This is the SINGLE SOURCE OF TRUTH for fertilizer name normalization.

IMPORTANT: This map must be updated during Phase 0 reconnaissance
by collecting all unique Tamil header names from the actual website.
"""

# Canonical mapping: Tamil name → standardized English name
_TAMIL_TO_ENGLISH = {
    # Nitrogenous
    'யூரியா':           'Urea',
    'அம்மோனியம் சல்பேட்': 'Ammonium Sulphate',

    # Phosphatic
    'டி ஏ பி':          'DAP',
    'டிஏபி':            'DAP',

    # Potassic
    'பொட்டாஸ்':         'MOP',
    'எம் ஓ பி':         'MOP',

    # Complex / NPK
    '16:16:16':          '16-16-16',
    '16-16-16':          '16-16-16',
    '10:26:26':          '10-26-26',
    '10-26-26':          '10-26-26',
    '20:20:0':           '20-20-0',
    '20-20-0':           '20-20-0',
    '14:35:14':          '14-35-14',
    '17:17:17':          '17-17-17',

    # Others
    'சிங்கிள் சூப்பர் பாஸ்பேட்': 'SSP',
    'ஜிப்சம்':           'Gypsum',
}

# Also handle case/whitespace variations
_NORMALIZED_MAP = {k.strip().lower(): v for k, v in _TAMIL_TO_ENGLISH.items()}


def normalize_fertilizer_name(tamil_name: str) -> str | None:
    """
    Convert Tamil fertilizer name to standardized English name.
    Returns None if the name is unrecognized (logged for review).
    """
    cleaned = tamil_name.strip().lower()

    # Direct lookup
    if cleaned in _NORMALIZED_MAP:
        return _NORMALIZED_MAP[cleaned]

    # Check if it's already an English name (e.g., 'Urea', 'DAP')
    english_set = set(_TAMIL_TO_ENGLISH.values())
    if tamil_name.strip() in english_set:
        return tamil_name.strip()

    # Unknown — log it so we can add it to the map
    import logging
    logging.getLogger(__name__).warning(
        f"UNKNOWN fertilizer name: '{tamil_name}' — add to fertilizer_map.py"
    )
    return tamil_name.strip()  # pass through as-is rather than dropping data
```

**Implementation** — `parser/data_cleaner.py`:

```python
class DataCleaner:
    """Utilities for cleaning scraped text values."""

    @staticmethod
    def parse_number_from_text(text: str) -> float:
        """
        Robustly parse numeric text from HTML.
        '1,650'  → 1650.0
        ''       → 0.0
        'N/A'    → 0.0
        '-'      → 0.0
        '1650.5' → 1650.5
        """
        if not text:
            return 0.0
        text = text.strip()
        if text in ('', 'N/A', '-', '--', 'nil', 'Nil', 'NIL'):
            return 0.0
        # Remove commas and spaces
        text = text.replace(',', '').replace(' ', '')
        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def clean_phone(text: str) -> str:
        """Extract 10-digit Indian mobile number."""
        import re
        match = re.search(r'[6-9]\d{9}', text)
        return match.group(0) if match else ''
```

---

### Phase 3: Normalizer + Database Storage

**Priority**: 🟡 HIGH

**Purpose**: Store parsed data in a properly normalized PostgreSQL database with a fertilizer master table and robust deduplication.

**Revised ER Diagram**:

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│  districts   │       │   blocks     │       │    dealers       │
├──────────────┤       ├──────────────┤       ├──────────────────┤
│ id (PK)      │──┐    │ id (PK)      │──┐    │ id (PK)          │
│ code (UQ)    │  │    │ code         │  │    │ dealer_code (UQ+)│← from (999210)
│ name_ta      │  │    │ name_ta      │  │    │ name_ta          │
│ name_en      │  │    │ name_en      │  │    │ contact          │
│ created_at   │  │    │ district_id  │──┘    │ address          │
└──────────────┘  │    │  (FK)        │       │ block_id (FK) ───┘
                  │    │ UNIQUE(code, │       │ created_at       │
                  │    │  district_id)│       │ updated_at       │
                  │    │ created_at   │       │ UNIQUE(dealer_   │
                  │    └──────────────┘       │  code, block_id) │
                  │                           └──────────────────┘
                  │                                    │
                  │    ┌───────────────────┐            │
                  │    │  fertilizers      │            │
                  │    │  (MASTER TABLE)   │            │
                  │    ├───────────────────┤            │
                  │    │ id (PK)           │            │
                  │    │ code (UQ)         │  'DAP'     │
                  │    │ name_en           │  'Di-Amm.' │
                  │    │ name_ta           │  'டி ஏ பி' │
                  │    │ category          │  'Phosph.' │
                  │    └────────┬──────────┘            │
                  │             │                       │
                  │    ┌────────┴──────────────────┐    │
                  │    │   fertilizer_stock        │    │
                  │    │   (FACT TABLE)            │    │
                  │    ├───────────────────────────┤    │
                  │    │ id (PK)                   │    │
                  │    │ dealer_id (FK) ───────────┘    │
                  │    │ fertilizer_id (FK) ────────────┘
                  │    │ quantity_kg  DECIMAL(10,2) │
                  │    │ scrape_date  DATE          │← one entry per day
                  │    │ scrape_run_id (FK)         │
                  │    │ created_at                 │
                  │    │ UNIQUE(dealer_id,          │
                  │    │   fertilizer_id,           │
                  │    │   scrape_date)             │
                  │    └───────────────────────────┘
                  │
                  │    ┌───────────────────────────┐
                  │    │   scrape_runs             │
                  │    ├───────────────────────────┤
                  │    │ id (PK)                   │
                  │    │ started_at  TIMESTAMP     │
                  │    │ completed_at TIMESTAMP    │
                  │    │ status      VARCHAR(20)   │ running/success/partial/failed
                  │    │ total_districts INTEGER   │
                  │    │ total_blocks    INTEGER   │
                  │    │ total_dealers   INTEGER   │
                  │    │ total_stocks    INTEGER   │
                  │    │ failed_districts INTEGER  │
                  │    │ failed_blocks   INTEGER   │
                  │    │ error_log       TEXT       │
                  │    └───────────────────────────┘
                  │
                  │    ┌───────────────────────────┐
                  │    │   scrape_checkpoints      │
                  │    │   (NEW — for resumability)│
                  │    ├───────────────────────────┤
                  │    │ id (PK)                   │
                  │    │ scrape_run_id (FK)        │
                  │    │ district_code VARCHAR(10) │
                  │    │ block_code    VARCHAR(10) │
                  │    │ status        VARCHAR(20) │ success/failed/skipped
                  │    │ dealers_found INTEGER     │
                  │    │ completed_at  TIMESTAMP   │
                  │    │ UNIQUE(scrape_run_id,     │
                  │    │  district_code,block_code)│
                  │    └───────────────────────────┘
```

**Key schema changes vs original**:

| Change | Reasoning |
|---|---|
| Added `fertilizers` master table | Prevents free-text inconsistency; enables Tamil↔English lookup |
| `fertilizer_stock.fertilizer_name` → `fertilizer_id` (FK) | Referential integrity, no more "DAP" vs "D.A.P" drift |
| Dealer UNIQUE key: `(dealer_code, block_id)` | `dealer_code` (from card headers) is reliable; `license_no` isn't visible |
| Added `name_ta` + `name_en` columns | Bilingual support for Tamil source data + English dashboard |
| Added `scrape_checkpoints` table | Enables resume-on-failure without re-scraping completed blocks |
| Richer `scrape_runs` metadata | Track per-level success/failure counts for observability |
| Added `updated_at` on dealers | Track when dealer info was last refreshed |

**SQL for the new `fertilizers` and `scrape_checkpoints` tables**:

```sql
-- FERTILIZERS MASTER TABLE (NEW)
CREATE TABLE fertilizers (
    id            SERIAL PRIMARY KEY,
    code          VARCHAR(50) UNIQUE NOT NULL,    -- 'DAP', 'UREA', 'MOP'
    name_en       VARCHAR(100) NOT NULL,          -- 'Di-Ammonium Phosphate'
    name_ta       VARCHAR(100),                   -- 'டி ஏ பி'
    category      VARCHAR(50),                    -- 'Phosphatic', 'Nitrogenous'
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Pre-seed with known fertilizers
INSERT INTO fertilizers (code, name_en, name_ta, category) VALUES
    ('UREA',     'Urea',                    'யூரியா',              'Nitrogenous'),
    ('DAP',      'Di-Ammonium Phosphate',   'டி ஏ பி',            'Phosphatic'),
    ('MOP',      'Muriate of Potash',       'பொட்டாஸ்',           'Potassic'),
    ('16-16-16', 'NPK 16-16-16',            '16:16:16',            'Complex'),
    ('10-26-26', 'NPK 10-26-26',            '10:26:26',            'Complex'),
    ('20-20-0',  'NPK 20-20-0',             '20:20:0',             'Complex'),
    ('SSP',      'Single Super Phosphate',  'சிங்கிள் சூப்பர் பாஸ்பேட்', 'Phosphatic'),
    ('GYPSUM',   'Gypsum',                  'ஜிப்சம்',             'Soil Amendment');

-- SCRAPE CHECKPOINTS TABLE (NEW)
CREATE TABLE scrape_checkpoints (
    id             SERIAL PRIMARY KEY,
    scrape_run_id  INTEGER REFERENCES scrape_runs(id),
    district_code  VARCHAR(10) NOT NULL,
    block_code     VARCHAR(10) NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending',   -- pending/success/failed
    dealers_found  INTEGER DEFAULT 0,
    error_message  TEXT,
    completed_at   TIMESTAMP,
    UNIQUE(scrape_run_id, district_code, block_code)
);

-- INDEX for fast checkpoint lookups
CREATE INDEX idx_checkpoint_run ON scrape_checkpoints(scrape_run_id, status);
```

---

### Phase 4: Checkpoint & Recovery System

**Priority**: 🟡 HIGH

**Purpose**: Make the pipeline resumable. If a scrape run fails midway, it can restart from where it left off instead of re-scraping everything.

**How it works**:

```
┌──────────────────────────────────────────────────────────┐
│                  CHECKPOINT FLOW                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Before scraping (district, block):                      │
│    1. Check: does checkpoint exist for today's run?      │
│       ├─ YES + status=success → SKIP (already done)     │
│       └─ NO or status=failed  → SCRAPE                  │
│                                                          │
│  After scraping (district, block):                       │
│    2. Write checkpoint: status=success, dealers_found=N  │
│                                                          │
│  On error:                                               │
│    3. Write checkpoint: status=failed, error_message=... │
│    4. Continue to next (district, block)                 │
│                                                          │
│  On resume:                                              │
│    5. Load all checkpoints for today's run_id            │
│    6. Skip all status=success pairs                      │
│    7. Retry all status=failed pairs                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Implementation** — `pipeline/checkpoint.py`:

```python
class CheckpointManager:
    """Track scraping progress per (district, block) pair."""

    def __init__(self, db_ops, run_id: int):
        self.db = db_ops
        self.run_id = run_id
        self._completed = set()  # Set of (dist_code, block_code) already done
        self._load_existing()

    def _load_existing(self):
        """Load checkpoints from DB for current run."""
        rows = self.db.get_checkpoints(self.run_id, status='success')
        self._completed = {(r.district_code, r.block_code) for r in rows}

    def is_done(self, district_code: str, block_code: str) -> bool:
        """Check if this (district, block) already scraped successfully."""
        return (district_code, block_code) in self._completed

    def mark_success(self, district_code: str, block_code: str, dealers_found: int):
        """Record successful scrape of a block."""
        self.db.upsert_checkpoint(
            self.run_id, district_code, block_code,
            status='success', dealers_found=dealers_found
        )
        self._completed.add((district_code, block_code))

    def mark_failed(self, district_code: str, block_code: str, error: str):
        """Record failed scrape of a block."""
        self.db.upsert_checkpoint(
            self.run_id, district_code, block_code,
            status='failed', error_message=error
        )
```

---

### Phase 5: Pipeline Orchestrator (Revised)

**Priority**: 🟡 HIGH

**Purpose**: Tie everything together — session → scrape → parse → normalize → store, with checkpointing and per-block error isolation.

**Implementation** — `pipeline/orchestrator.py`:

```python
import logging
from datetime import date, datetime
from scraper.session_manager import SessionManager
from parser.card_parser import CardParser
from parser.fertilizer_map import normalize_fertilizer_name
from database.operations import DBOperations
from pipeline.checkpoint import CheckpointManager

log = logging.getLogger(__name__)


class ScrapingPipeline:
    """
    MASTER ORCHESTRATOR
    Ties together: Session → Scrape → Parse → Normalize → Store
    With checkpointing and per-block error isolation.
    """

    def __init__(self, rate_limit: float = 2.0):
        self.session = SessionManager()
        self.parser = CardParser()
        self.db = DBOperations()
        self.rate_limit = rate_limit

    def run(self, resume_run_id: int | None = None):
        """
        Execute a full scraping run.

        Args:
            resume_run_id: If provided, resume a previous failed run
                           instead of starting fresh.
        """
        # --- Setup ---
        if resume_run_id:
            run_id = resume_run_id
            log.info(f"RESUMING run {run_id}")
        else:
            run_id = self.db.create_scrape_run()
            log.info(f"STARTING new run {run_id}")

        checkpoint = CheckpointManager(self.db, run_id)
        today = date.today()
        stats = {'districts': 0, 'blocks': 0, 'dealers': 0,
                 'stocks': 0, 'failed_blocks': 0}

        try:
            # --- Phase 0: Bootstrap session + get districts ---
            districts = self.session.bootstrap()
            log.info(f"Found {len(districts)} districts")

            for district in districts:
                stats['districts'] += 1

                try:
                    # --- Save district to DB ---
                    dist_id = self.db.upsert_district(
                        code=district['code'],
                        name_ta=district['name_ta']
                    )

                    # --- Get blocks for this district ---
                    blocks = self.session.get_blocks_for_district(district['code'])
                    log.info(f"  {district['name_ta']}: {len(blocks)} blocks")

                    for block in blocks:
                        # --- Checkpoint check ---
                        if checkpoint.is_done(district['code'], block['code']):
                            log.debug(f"    SKIP {block['name_ta']} (already done)")
                            continue

                        try:
                            # --- Save block to DB ---
                            block_id = self.db.upsert_block(
                                code=block['code'],
                                name_ta=block['name_ta'],
                                district_id=dist_id
                            )

                            # --- Fetch results HTML ---
                            html = self.session.fetch_results(
                                district['code'], block['code']
                            )

                            # --- Parse cards ---
                            dealers = self.parser.parse_results_page(
                                html, district, block
                            )
                            log.info(f"    {block['name_ta']}: {len(dealers)} dealers")

                            # --- Store each dealer + stocks ---
                            for dealer in dealers:
                                dealer_id = self.db.upsert_dealer(
                                    dealer_code=dealer['dealer_code'],
                                    name_ta=dealer['dealer_name'],
                                    contact=dealer['contact'],
                                    address=dealer['address'],
                                    block_id=block_id
                                )

                                for fert_name, quantity in dealer['stocks'].items():
                                    fert_id = self.db.get_or_create_fertilizer(fert_name)
                                    self.db.upsert_stock(
                                        dealer_id=dealer_id,
                                        fertilizer_id=fert_id,
                                        quantity=quantity,
                                        scrape_date=today,
                                        run_id=run_id
                                    )
                                    stats['stocks'] += 1

                                stats['dealers'] += 1

                            # --- Mark checkpoint success ---
                            checkpoint.mark_success(
                                district['code'], block['code'],
                                dealers_found=len(dealers)
                            )
                            stats['blocks'] += 1

                            # --- Rate limit ---
                            import time
                            time.sleep(self.rate_limit)

                        except Exception as e:
                            log.error(f"    FAILED {block['name_ta']}: {e}")
                            checkpoint.mark_failed(
                                district['code'], block['code'], str(e)
                            )
                            stats['failed_blocks'] += 1
                            continue

                except Exception as e:
                    log.error(f"  FAILED district {district['name_ta']}: {e}")
                    continue

            # --- Finalize ---
            final_status = 'success' if stats['failed_blocks'] == 0 else 'partial'
            self.db.complete_scrape_run(run_id, status=final_status, **stats)
            log.info(f"Run {run_id} completed: {final_status} | {stats}")

        except Exception as e:
            log.critical(f"Pipeline catastrophic failure: {e}")
            self.db.complete_scrape_run(run_id, status='failed')
            raise
```

---

## 5. Revised Project Structure

```
tfais/
│
├── config/
│   ├── settings.py                 # DB credentials, base URLs, timeouts, rate limits
│   └── .env                        # Secrets (not committed)
│
├── scraper/
│   ├── __init__.py
│   ├── session_manager.py          # [NEW] HTTP session, cookies, CSRF, form workflow
│   └── scraper.py                  # [REVISED] POST-based scraping, NOT URL-based
│   ▸ REMOVED: url_builder.py       # No longer needed (POST-based, not URL-based)
│   ▸ REMOVED: district_scraper.py  # Merged into session_manager.bootstrap()
│   ▸ REMOVED: block_scraper.py     # Merged into session_manager.get_blocks()
│   ▸ REMOVED: dealer_scraper.py    # Merged into session_manager.fetch_results()
│
├── parser/
│   ├── __init__.py
│   ├── card_parser.py              # [NEW] Replaces table_parser.py — card-based parsing
│   ├── fertilizer_map.py           # [NEW] Tamil → English name mapping dictionary
│   └── data_cleaner.py             # [REVISED] Added parse_number_from_text, clean_phone
│   ▸ REMOVED: table_parser.py      # Replaced by card_parser.py
│
├── database/
│   ├── __init__.py
│   ├── models.py                   # [REVISED] Added Fertilizer, ScrapeCheckpoint models
│   ├── connection.py               # DB engine + session factory
│   ├── operations.py               # [REVISED] Upsert uses dealer_code, fertilizer_id FK
│   └── migrations/                 # Alembic migrations
│
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py             # [REVISED] Per-block error isolation, checkpoint
│   └── checkpoint.py               # [NEW] Resume-on-failure capability
│
├── recon/                          # [NEW] Reconnaissance tooling
│   ├── save_samples.py             # Save sample HTML from each level (offline dev)
│   ├── discover_fertilizers.py     # Crawl all blocks, collect unique Tamil names
│   └── sample_html/               # Saved HTML files for offline parser development
│
├── logs/
│   └── scraper.log
│
├── tests/
│   ├── test_card_parser.py         # [RENAMED] Test card parsing, not table parsing
│   ├── test_fertilizer_map.py      # [NEW] Test Tamil→English mapping
│   ├── test_session_manager.py     # [NEW] Test session bootstrap, form workflow
│   ├── test_checkpoint.py          # [NEW] Test checkpoint resume logic
│   └── test_db.py
│
├── main.py                         # Entry point (supports --resume flag)
├── requirements.txt
└── README.md
```

**What was removed and why**:

| Removed File | Replacement | Why |
|---|---|---|
| `url_builder.py` | `session_manager.py` | URLs are POST-based, no URL construction needed |
| `district_scraper.py` | `session_manager.bootstrap()` | Districts come from dropdown, not URL crawling |
| `block_scraper.py` | `session_manager.get_blocks()` | Blocks come from AJAX POST, not URL crawling |
| `dealer_scraper.py` | `session_manager.fetch_results()` | Results come from form POST, not page navigation |
| `table_parser.py` | `card_parser.py` | Data is cards with mini-tables, not flat tables |

---

## 6. Concurrency Strategy (Optional Enhancement)

For production use, sequential scraping works but takes ~19 minutes. An async approach can cut this to ~6 minutes:

```python
# Async version (Phase 2 enhancement, not MVP)
import asyncio
import aiohttp

CONCURRENCY_LIMIT = 3  # Max 3 simultaneous requests (respectful)

async def scrape_block(session, semaphore, district, block):
    async with semaphore:
        # POST for results
        async with session.post(RESULTS_URL, data=form_data) as resp:
            html = await resp.text()
        await asyncio.sleep(1)  # rate limit even in async
        return parse_cards(html)

async def scrape_all_async(districts_blocks):
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with aiohttp.ClientSession() as session:
        tasks = [
            scrape_block(session, semaphore, d, b)
            for d, b in districts_blocks
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

> [!TIP]
> Start with the synchronous approach for MVP. Add async concurrency only after the sequential pipeline is proven stable.

---

## 7. Playwright Fallback Strategy

If the POST-based `requests` approach fails (e.g., the site validates JavaScript execution), implement a Playwright fallback:

```python
# scraper/playwright_fallback.py
from playwright.sync_api import sync_playwright

class PlaywrightScraper:
    """Fallback scraper using a real browser for JS-heavy pages."""

    def fetch_results(self, district_code, block_code):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(ENTRY_URL)

            # Select district from dropdown
            page.select_option('#district', district_code)
            page.wait_for_timeout(1000)  # wait for AJAX

            # Select block from dropdown
            page.select_option('#block', block_code)

            # Click search
            page.click('button[type="submit"]')
            page.wait_for_selector('.card', timeout=10000)

            html = page.content()
            browser.close()
            return html
```

---

## 8. Revised Execution Timeline

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  DAY  1     │███│    Phase 0: Recon — POST workflow discovery      │
│                   • Save sample HTMLs from each POST endpoint      │
│                   • Map all district IDs from dropdown             │
│                   • Discover all Tamil fertilizer names            │
│                   • Verify requests vs Playwright needed           │
│                                                                    │
│  DAY  2     │███│    Session Manager + Fertilizer Map              │
│                   • session_manager.py (bootstrap, getBlocks,      │
│                     fetchResults)                                  │
│                   • fertilizer_map.py (Tamil→English dictionary)   │
│                                                                    │
│  DAY  3-4   │█████│  Card Parser                                   │
│                   • card_parser.py (parse cards, dynamic headers)  │
│                   • data_cleaner.py (number parsing, phone clean)  │
│                   • Test against saved sample HTMLs                │
│                                                                    │
│  DAY  5-6   │█████│  Database Schema + Operations                  │
│                   • Create all tables (with fertilizers master)    │
│                   • operations.py (upsert with dealer_code key)    │
│                   • Seed fertilizers table                         │
│                                                                    │
│  DAY  7-8   │█████│  Pipeline Orchestrator + Checkpoint            │
│                   • orchestrator.py (full flow with error isolation)│
│                   • checkpoint.py (resume-on-failure)              │
│                                                                    │
│  DAY  9     │███│    End-to-End Test: 1 District                   │
│                   • Run full pipeline for 1 district               │
│                   • Validate DB records match website              │
│                   • Fix edge cases                                 │
│                                                                    │
│  DAY  10    │███│    Full Scrape + Validation                      │
│                   • Run for all 38 districts                       │
│                   • Spot-check 5 random dealers                    │
│                   • Verify checkpoint resume works                 │
│                                                                    │
│                                                                    │
│  TOTAL: ~10 working days for MVP                                   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 9. Verification Plan

### Unit Tests
| Test File | What It Verifies |
|---|---|
| `test_card_parser.py` | Card HTML → structured dict parsing, dynamic headers, edge cases |
| `test_fertilizer_map.py` | All known Tamil names map correctly, unknown names logged |
| `test_session_manager.py` | Bootstrap extracts districts, getBlocks returns blocks |
| `test_checkpoint.py` | Resume skips completed blocks, retries failed ones |

### Integration Tests
| Test | What It Verifies |
|---|---|
| Single-district pipeline | End-to-end: POST → Parse → DB for one district |
| Upsert idempotency | Running twice for same date doesn't create duplicates |
| Checkpoint resume | Kill mid-run → resume → no duplicate data |

### Manual Spot-Check
1. Pick 5 random dealers from the DB
2. Go to the website, search the same district+block
3. Verify stock numbers match exactly

---

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Website changes HTML structure | Medium | High | Save sample HTMLs, test parser against them weekly |
| IP gets rate-limited/blocked | Low | High | 2s delay, realistic UA, rotate IP if needed |
| New fertilizer type appears | High | Low | `fertilizer_map.py` logs unknowns, easy to add |
| CSRF token expires mid-scrape | Medium | Medium | Re-bootstrap session every N requests |
| Site goes down during scrape | Medium | Medium | Checkpoint system enables resume |
| Tamil encoding issues | Low | Medium | Force UTF-8 everywhere, test with தமிழ் strings |
