# 🔬 Subsection Parser Logic — Detailed Specifications (v2.2)

> v2.2 — Final revision. `safe_parse_number` returns `None` (not 0.0), validation thresholds are parser-level constants, `retry_request()` wired to all HTTP calls, anomalies stored in structured `scrape_anomalies` table.

---

## Table of Contents

1. [Fertilizer Stock Position Parser](#1-fertilizer-stock-position-parser) ✅
2. [Fertilizer Price Parser](#2-fertilizer-price-parser) ✅
3. [Biofertilizer & MN Mixture Parser](#3-biofertilizer--mn-mixture-parser) 🔮
4. [Shared Utilities](#4-shared-utilities)
5. [Parser Comparison Matrix](#5-parser-comparison-matrix)

---

## 1. Fertilizer Stock Position Parser

**File**: `tfais/sections/fertilizer/parsers/stock_position.py`
**Status**: ✅ Migrated from `parser/card_parser.py` (old file deleted)

### 1.1 Data Source

| Property | Value |
|---|---|
| Entry URL | `GET /people_app/fertilizer/stock/en/20/2020` |
| Blocks URL | `POST /people_app/Fertilizer/getBlocks/{district_id}` |
| Results URL | `POST /people_app/Fertilizer/result/en` |
| Auth | Session cookie (`ci_session`) |

### 1.2 HTTP Ownership

This parser **internally owns** a `requests.Session()`. No shared HttpClient.

```python
class StockPositionParser:
    # --- Validation thresholds (parser-level constants, not magic numbers) ---
    COUNT_DROP_THRESHOLD = 0.5     # 50% drop = catastrophic (15k records)
    MAX_NULL_RATIO = 0.1           # >10% NULLs = data quality issue

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._csrf_token = None
        self._hidden_fields = {}
```

Session management (bootstrap, CSRF capture, cookie persistence) all live inside this parser — not in a shared service.

### 1.3 HTTP Workflow

```
1. GET entry page → capture session, CSRF, district list [via retry_request()]
2. For each district: POST getBlocks/{id} → block list (JSON) [via retry_request()]
3. For each (district, block):
   - Check checkpoint → skip if done
   - POST /Fertilizer/result/en → HTML with ng-init JSON [via retry_request()]
   - rate_limit(2s)
```

### 1.4 Parsing Algorithm

```
HTML → find ng-init div → extract JSON → per-dealer records

Strategy 1 (preferred): ng-init JSON
  <div ng-init='fert_list={"0": {"tamil_agency": "...", "fert": {...}}, ...}'>
  
  Steps:
  1. Find tag with ng-init attribute
  2. Extract JSON after "fert_list="
  3. Sanitize: collapse literal \n to spaces
  4. json.loads() → dict
  5. Per dealer: extract identity, stocks (qty × 1000 for kg)
  6. Compute structure signature (MD5 of sorted headers)

Strategy 2 (fallback): HTML card parsing
  Steps:
  1. Triage page: HAS_RESULTS | EMPTY | ERROR
  2. Discover cards via selector chain (card → panel → col → structural)
  3. Per card: extract dealer identity, address, contact, stock table
  4. Row classification: cell-majority numeric test
  5. Header extraction (LAST header row) → value mapping
```

### 1.5 Tamil→English Mapping

Kept **inside this parser** (it's the only consumer):

```python
# Internal to stock_position.py
_FERTILIZER_NAME_MAP = {
    "Neem Coated Urea(45 Kg)": "Neem Coated Urea (45 Kg)",
    "DAP(50 Kg)":              "DAP (50 Kg)",
    "யூரியா":                  "Urea",
    "டி ஏ பி":                 "DAP",
    "பொட்டாஸ்":                "MOP",
    # ... (more as discovered)
}
```

Not extracted into a shared `DataNormalizer` — there's only one consumer today.

### 1.6 Validation

```python
def validate(self, records: list[DealerRecord], session) -> list[dict]:
    anomalies = []
    
    # Run-level: compare count to previous (uses class constant)
    prev = get_previous_count(session, "stock_position")
    if prev > 0 and len(records) < prev * self.COUNT_DROP_THRESHOLD:
        anomalies.append({
            "parser_id": self.parser_id,
            "anomaly_type": "count_drop",
            "detail": f"Dealer count: {prev} → {len(records)}",
            "severity": "critical",
        })
    
    # Record-level: check NULL ratio from safe_parse_number
    null_count = sum(1 for r in records 
                     if all(v is None for v in r.stocks.values()))
    if records and null_count / len(records) > self.MAX_NULL_RATIO:
        anomalies.append({
            "parser_id": self.parser_id,
            "anomaly_type": "null_ratio",
            "detail": f"{null_count}/{len(records)} records all-NULL",
            "severity": "warning",
        })
    
    # Page-level: flag districts that went from data → empty
    for district_code, count in self._district_counts.items():
        prev_district = get_previous_district_count(session, district_code)
        if prev_district > 0 and count == 0:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "district_empty",
                "detail": f"District {district_code}: {prev_district} → 0",
                "severity": "critical",
            })
    
    return anomalies
```

### 1.7 Checkpoints

Owned by this parser. Work unit key = `{district_code}:{block_code}`.

```python
# After successfully scraping a block:
mark_checkpoint(session, run_id, 
    parser_id="stock_position",
    work_unit_key=f"{district_code}:{block_code}",
    status="done", records_found=len(records))

# Before scraping, check if already done:
if is_checkpoint_done(session, run_id, 
    parser_id="stock_position", 
    work_unit_key=f"{district_code}:{block_code}"):
    continue  # skip
```

### 1.8 Persistence

```
DealerRecord → upsert_district → upsert_block → upsert_dealer → insert_stock_batch
```

Dedup: `UNIQUE(dealer_id, fertilizer_name, scrape_date)` — re-runs on same day update existing rows.

### 1.9 Edge Cases

| Case | Handling |
|---|---|
| Literal `\n` in JSON values | Collapsed to space before `json.loads()` |
| Empty `fert` dict | Valid record with 0 stocks |
| Missing `dealer_id` | Stored as "" — partial unique index allows it |
| Header/value count mismatch | Truncate to min length, log warning |
| Session expired mid-run | Re-bootstrap (parser owns the session) |
| `safe_parse_number` returns `None` | Stock parser uses `or 0.0` (zero is valid stock) |
| District returns 0 but had data | **Validation flags as `district_empty` anomaly** |

---

## 2. Fertilizer Price Parser

**File**: `tfais/sections/fertilizer/parsers/fertilizer_price.py`
**Status**: ✅ To be implemented

### 2.1 Data Source

| Property | Value |
|---|---|
| Entry URL | `GET /people_app/fertilizer_price/index/en/20/2020` |
| Price API | `POST /people_app/fertilizer_price/fertDetails/{fert_id}` |
| Auth | **None** — stateless POST |

### 2.2 HTTP Ownership

**No session.** Uses `retry_request()` wrapper around `requests.post()`. Each call is independent.

```python
class FertilizerPriceParser:
    parser_id = "fertilizer_price"
    
    # --- Validation thresholds ---
    COUNT_DROP_THRESHOLD = 0.3     # 30% drop (500 records, more volatile than stock)
    PRICE_SPIKE_MULTIPLIER = 10    # >10x median = anomaly
    MAX_NULL_RATIO = 0.2           # >20% NULL prices = data quality issue
    
    def _fetch_prices(self, product_id: int) -> list[dict]:
        url = f"{PRICE_API_URL}/{product_id}"
        resp = retry_request(
            lambda: requests.post(url, headers=DEFAULT_HEADERS, timeout=30)
        )
        resp.raise_for_status()
        return resp.json()
```

### 2.3 HTTP Workflow

```
1. GET entry page → parse <select#fert_id> → product catalog (runtime discovery)
2. For each product_id:
   POST /fertilizer_price/fertDetails/{product_id}
   rate_limit(1s)
   → JSON array: [{"company": "IFFCO", "price": "266.50"}, ...]
```

Product catalog is **discovered at runtime** from the `<select>` element. Not hardcoded.

### 2.4 Known Products (reference only)

```
1: UREA, 2: DAP, 3: MOP, 4: Complex 10:26:26, 5: Complex 14:35:14,
6: Complex 17:17:17, 7: Complex 20:20:0, 8: Complex 24:24:0,
9: Complex 28:28:0, 10: Complex 15:15:15, 11: Complex 19:19:19,
12: Complex 12:32:16, 13: Complex 16:16:16, 14: Complex 16:20:0:13,
15: Complex 20:20:0:13, 16: Complex 14:28:14, 17: Complex 15:15:15:09,
18: Factamphos 20:20:0:13, 19: CITY COMPOST, 20: Ammonium Chloride,
22: SSP Powdered, 23: SSP Granulated, 24: PROM, 25: Organic Plus
```

### 2.5 Response Structure

```json
// POST /fertilizer_price/fertDetails/1  (UREA)
[
    {"company": "IFFCO", "price": "266.50"},
    {"company": "KRIBHCO", "price": "266.50"},
    {"company": "NFL(Naya Nangal)", "price": "266.50"}
]
```

- Price is Rs per 50 kg bag
- Labels are English (no Tamil mapping needed)
- Some products return `[]` — no companies supply them

### 2.6 Parsing Algorithm

```
FETCH:
  GET index page → parse <select#fert_id> → {id: name, ...} [via retry_request()]
  For each product:
    POST fertDetails/{id} → JSON array [via retry_request()]
    rate_limit(1s)
    Checkpoint after each product

PARSE:
  For each JSON entry:
    company = entry["company"].strip()
    price = safe_parse_number(entry["price"])  # returns None for garbage, float for valid
    → PriceRecord(product_id, product_name, company, price)

VALIDATE:
  Compare total record count vs previous run (COUNT_DROP_THRESHOLD)
  Flag any prices that are None (NULL ratio > MAX_NULL_RATIO)
  Flag prices > PRICE_SPIKE_MULTIPLIER × median
  Flag negative prices
  Flag new products discovered

PERSIST:
  INSERT into fertilizer_prices
  ON CONFLICT (product_id, company, scrape_date) UPDATE price
```

### 2.7 Data Model

```python
@dataclass
class PriceRecord:
    product_id: int              # From <select> value
    product_name: str            # "UREA", "DAP", etc.
    company: str                 # "IFFCO", "KRIBHCO", etc.
    price_per_50kg: float | None  # Rs per 50 kg bag (None = unparseable)
    scraped_at: datetime
```

> **Note:** `price_per_50kg` is `float | None`. `safe_parse_number` returns `None` for garbage values (`"*"`, `"N/A"`, `""`). The caller does NOT coerce to 0.0 — unknown price ≠ free product. `None` is persisted as `NULL` in the DB.

### 2.8 Validation

```python
def validate(self, records: list[PriceRecord], session) -> list[dict]:
    anomalies = []
    
    # Run-level: count comparison (uses class constant)
    prev_count = get_previous_count(session, "fertilizer_price")
    if prev_count > 0 and len(records) < prev_count * self.COUNT_DROP_THRESHOLD:
        anomalies.append({
            "parser_id": self.parser_id,
            "anomaly_type": "count_drop",
            "detail": f"{prev_count} → {len(records)}",
            "severity": "critical",
        })
    
    # Record-level: NULL ratio (safe_parse_number returned None)
    null_prices = [r for r in records if r.price_per_50kg is None]
    if records and len(null_prices) / len(records) > self.MAX_NULL_RATIO:
        anomalies.append({
            "parser_id": self.parser_id,
            "anomaly_type": "null_ratio",
            "detail": f"{len(null_prices)}/{len(records)} prices are NULL",
            "severity": "warning",
        })
    
    # Record-level: price range checks
    valid_prices = [r.price_per_50kg for r in records
                    if r.price_per_50kg is not None and r.price_per_50kg > 0]
    if valid_prices:
        median = sorted(valid_prices)[len(valid_prices) // 2]
        for r in records:
            if r.price_per_50kg is not None and r.price_per_50kg < 0:
                anomalies.append({
                    "parser_id": self.parser_id,
                    "anomaly_type": "negative_price",
                    "detail": f"{r.product_name}/{r.company}: {r.price_per_50kg}",
                    "severity": "warning",
                })
            elif (r.price_per_50kg is not None and
                  r.price_per_50kg > median * self.PRICE_SPIKE_MULTIPLIER):
                anomalies.append({
                    "parser_id": self.parser_id,
                    "anomaly_type": "price_spike",
                    "detail": f"{r.product_name}/{r.company}: {r.price_per_50kg} (median={median})",
                    "severity": "warning",
                })
    
    # Product discovery: flag new products
    prev_products = get_previous_product_ids(session)
    new_products = {r.product_id for r in records} - prev_products
    if new_products:
        anomalies.append({
            "parser_id": self.parser_id,
            "anomaly_type": "new_products",
            "detail": f"New product IDs: {new_products}",
            "severity": "info",
        })
    
    return anomalies
```

### 2.9 Checkpoints

Work unit key = `product:{product_id}`.

```python
# After each product:
mark_checkpoint(session, run_id,
    parser_id="fertilizer_price",
    work_unit_key=f"product:{product_id}",
    status="done", records_found=len(entries))

# On resume: skip products already done
if is_checkpoint_done(session, run_id,
    parser_id="fertilizer_price",
    work_unit_key=f"product:{product_id}"):
    continue
```

### 2.10 Persistence

```python
def persist(self, records: list[PriceRecord], session, run_id) -> int:
    inserted = 0
    for r in records:
        existing = session.scalar(
            select(FertilizerPrice).where(
                FertilizerPrice.product_id == r.product_id,
                FertilizerPrice.company == r.company,
                FertilizerPrice.scrape_date == r.scraped_at.date(),
            )
        )
        if existing:
            existing.price_per_50kg = r.price_per_50kg
        else:
            session.add(FertilizerPrice(
                product_id=r.product_id,
                product_name=r.product_name,
                company=r.company,
                price_per_50kg=r.price_per_50kg,
                scrape_date=r.scraped_at.date(),
                scrape_run_id=run_id,
            ))
            inserted += 1
    return inserted
```

### 2.11 Edge Cases

| Case | Handling |
|---|---|
| Empty JSON array `[]` | Skip product, log INFO |
| `price: ""` or `price: "*"` | `safe_parse_number` returns `None` → persisted as `NULL` |
| `price: "0"` | `safe_parse_number` returns `0.0` (valid — zero is a real price) |
| Missing `company` key | Skip entry, log ERROR |
| Malformed JSON | Catch `JSONDecodeError`, checkpoint as error, continue |
| Price string with commas | `safe_parse_number("1,266.50")` → 1266.5 |
| Server returns HTML not JSON | Detect via content-type, skip product |
| Transient HTTP 500 | **`retry_request()` retries 3x with backoff** |
| **Negative price** | **Persist, validation writes `negative_price` to `scrape_anomalies`** |
| **Price >10x median** | **Persist, validation writes `price_spike` to `scrape_anomalies`** |
| **>20% prices are None** | **Validation writes `null_ratio` to `scrape_anomalies`** |
| New product in `<select>` | **Discovered automatically, `new_products` anomaly** |

### 2.12 Full Implementation Skeleton

```python
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from tfais.core.http_utils import DEFAULT_HEADERS, rate_limit, retry_request
from tfais.config.settings import BASE_URL

log = logging.getLogger(__name__)

ENTRY_URL = f"{BASE_URL}/fertilizer_price/index/en/20/2020"
PRICE_API_URL = f"{BASE_URL}/fertilizer_price/fertDetails"


@dataclass
class PriceRecord:
    product_id: int
    product_name: str
    company: str
    price_per_50kg: float
    scraped_at: datetime


class FertilizerPriceParser:
    parser_id = "fertilizer_price"
    parser_name = "Fertilizer Price Details"
    
    # --- Validation thresholds ---
    COUNT_DROP_THRESHOLD = 0.3
    PRICE_SPIKE_MULTIPLIER = 10
    MAX_NULL_RATIO = 0.2
    
    def run(self, db_session_factory, run_id) -> dict:
        """Full pipeline: fetch → parse → validate → persist."""
        raw = self.fetch()
        records = self.parse(raw)
        
        with db_session_factory() as session:
            anomalies = self.validate(records, session)
            count = self.persist(records, session, run_id)
        
        return {
            "parser_id": self.parser_id,
            "records": len(records),
            "persisted": count,
            "anomalies": anomalies,
        }
    
    def fetch(self) -> list[dict]:
        # 1. Discover products from page
        resp = retry_request(
            lambda: requests.get(ENTRY_URL, headers=DEFAULT_HEADERS, timeout=30)
        )
        resp.raise_for_status()
        products = self._extract_products(BeautifulSoup(resp.text, "lxml"))
        
        # 2. Fetch prices per product (with retry on each call)
        results = []
        for pid, pname in products.items():
            try:
                resp = retry_request(
                    lambda pid=pid: requests.post(
                        f"{PRICE_API_URL}/{pid}",
                        headers=DEFAULT_HEADERS, timeout=30
                    )
                )
                resp.raise_for_status()
                entries = resp.json()
                results.append({
                    "product_id": pid,
                    "product_name": pname,
                    "entries": entries if isinstance(entries, list) else [],
                })
            except Exception as exc:
                log.error(f"Failed product {pname} (id={pid}): {exc}")
            rate_limit(1)
        
        return results
    
    def parse(self, raw: list[dict]) -> list[PriceRecord]:
        records = []
        now = datetime.now(tz=timezone.utc)
        for item in raw:
            for entry in item["entries"]:
                company = entry.get("company", "").strip()
                if not company:
                    continue
                records.append(PriceRecord(
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    company=company,
                    price_per_50kg=safe_parse_number(entry.get("price", "0")),
                    scraped_at=now,
                ))
        return records
    
    def validate(self, records, session) -> list[str]:
        # ... (see section 2.8 above)
        return []
    
    def persist(self, records, session, run_id) -> int:
        # ... (see section 2.10 above)
        return 0
    
    def _extract_products(self, soup) -> dict[int, str]:
        catalog = {}
        select = soup.find("select", id="fert_id")
        if not select:
            log.error("Product <select#fert_id> not found")
            return catalog
        for option in select.find_all("option"):
            val = option.get("value", "").strip()
            if val and val != "0":
                try:
                    catalog[int(val)] = option.get_text(strip=True)
                except ValueError:
                    continue
        log.info(f"Discovered {len(catalog)} products")
        return catalog
```

---

## 3. Biofertilizer & MN Mixture Parser

**File**: `tfais/sections/fertilizer/parsers/biofertilizer.py`
**Status**: 🔮 Stub — deferred

### 3.1 Why Deferred

1. **Different domain**: `tnagrisnet.tn.gov.in` — not the `115.243.209.84` server
2. **Angular SPA**: `mat-select` components, async data loading — BeautifulSoup can't parse
3. **REST API exists** but needs investigation on request body format
4. **Need a different parser engine**: Either direct API calls or Playwright

### 3.2 Known API Endpoints

| Endpoint | Method | URL |
|---|---|---|
| District list | GET | `https://tnagrisnet.tn.gov.in/agri_api/uatt/fert/distList` |
| Stock data | POST | `https://tnagrisnet.tn.gov.in/agri_api/uatt/fert/stockAvailability` |

### 3.3 Stub Implementation

```python
class BiofertilizerParser:
    parser_id = "biofertilizer"
    parser_name = "Biofertilizer & MN Mixture Stock"
    
    def run(self, db_session_factory, run_id) -> dict:
        raise NotImplementedError(
            "Deferred — requires REST API calls or Playwright. "
            "BeautifulSoup cannot parse this Angular SPA. "
            "See docs/subsection_parser_logic.md section 3."
        )
```

### 3.4 DB Table (created but empty)

```sql
CREATE TABLE biofertilizer_stock (
    id             BIGSERIAL PRIMARY KEY,
    district_code  VARCHAR(20) NOT NULL,
    district_name  VARCHAR(200) NOT NULL,
    product_name   VARCHAR(200) NOT NULL,
    quantity       FLOAT NOT NULL DEFAULT 0.0,
    unit           VARCHAR(20) NOT NULL DEFAULT 'KG',
    scrape_date    DATE NOT NULL,
    scrape_run_id  INTEGER REFERENCES scrape_runs(id),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (district_code, product_name, scrape_date)
);
```

### 3.5 Prerequisites Before Implementation

1. Inspect `stockAvailability` POST body format (browser network tab)
2. Test if `requests` works or if CORS/auth blocks it
3. Decide: plain `requests` (preferred) vs Playwright (fallback)
4. The parser will own its own HTTP — no shared client needed

---

## 4. Shared Utilities

### 4.1 `core/http_utils.py`

Only truly shared, thin utilities. Not a class.

```python
"""Shared HTTP utilities — ~20 lines total."""
import time
import logging

log = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}


def retry_request(fn, max_retries=3, backoff=2):
    """Retry a callable with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = backoff ** attempt
            log.warning(f"Retry {attempt+1}/{max_retries} after {wait}s: {exc}")
            time.sleep(wait)


def rate_limit(seconds=2):
    """Polite delay between requests."""
    time.sleep(seconds)
```

### 4.2 `core/metadata.py`

Extracts "Last update date" from pages:

```python
import re
from datetime import date, datetime

DATE_PATTERNS = [
    r"Last\s+update\s+date\s*:\s*(\d{2}-\d{2}-\d{4})",
    r"கடைசி\s+புதுப்பிக்கப்பட்ட\s+நாள்\s*:\s*(\d{2}-\d{2}-\d{4})",
]

def extract_last_updated(html: str) -> date | None:
    """Parse 'Last update date :29-03-2026' → datetime.date."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, html)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d-%m-%Y").date()
            except ValueError:
                continue
    return None
```

### 4.3 `safe_parse_number()`

Returns `None` for unparseable values — callers decide what unknown means.

```python
def safe_parse_number(text: str) -> float | None:
    """
    Robust numeric parsing. Returns None for garbage, not 0.0.
    
    Callers decide semantics:
      Stock:  qty = safe_parse_number(v) or 0.0   # zero is valid stock
      Price:  price = safe_parse_number(v)         # None = unknown, persisted as NULL
    
    Examples:
        '1650'     → 1650.0
        '1,650'    → 1650.0
        '0'        → 0.0        (valid zero)
        ''         → None       (no data)
        '-'        → None       (no data)
        'N/A'      → None       (no data)
        '*'        → None       (no data)
    """
    if not text or not text.strip():
        return None
    text = text.strip()
    if text in ("-", "--", "N/A", "nil", "Nil", "NIL", "*"):
        return None
    text = text.replace(",", "").replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return None
```

### 4.4 Error Snapshots

```python
def save_snapshot(html: str, context: str, error: str, parser_id: str = ""):
    """Save failed HTML to logs/failed_cards/ for offline debugging."""
    os.makedirs("logs/failed_cards", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    prefix = f"{parser_id}_" if parser_id else ""
    path = f"logs/failed_cards/{prefix}{context}_{ts}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- ERROR: {error} -->\n{html}")
```

---

## 5. Parser Comparison Matrix

| Feature | Stock Position | Fertilizer Price | Biofertilizer |
|---|---|---|---|
| **Status** | ✅ Implemented | ✅ To implement | 🔮 Stub |
| **HTTP** | `requests.Session()` + `retry_request()` | `retry_request()` + `requests.post()` | TBD |
| **Session needed** | Yes (cookies, CSRF) | No | No |
| **Parser engine** | BeautifulSoup + json | requests + json | TBD |
| **Iteration** | District → Block → POST | Product → POST | District → POST |
| **Records/run** | ~15,000+ | ~500 | TBD |
| **Rate limit** | 2s | 1s | 0.5s |
| **Checkpoint key** | `{district}:{block}` | `product:{id}` | `district:{code}` |
| **Dedup key** | dealer_id + fert + date | product_id + company + date | district + product + date |
| **Validation thresholds** | `DROP=0.5`, `NULL=0.1` | `DROP=0.3`, `SPIKE=10x`, `NULL=0.2` | TBD |
| **`safe_parse_number` semantics** | `or 0.0` (zero is valid stock) | Keep `None` (unknown ≠ free) | TBD |
| **Anomaly output** | `list[dict]` → `scrape_anomalies` table | `list[dict]` → `scrape_anomalies` table | TBD |
| **Tamil→English map** | Internal to parser | Not needed (English native) | Not needed |
| **DB table** | `fertilizer_stock` | `fertilizer_prices` | `biofertilizer_stock` |
