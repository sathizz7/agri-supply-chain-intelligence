# 🔍 Senior Review: Initial LLD — Backend Scraper Pipeline

> **Reviewer Role**: Senior Data Scientist  
> **Documents Reviewed**: [requirement.md](file:///d:/Mini-proj/dashboard/docs/requirement.md), [intial_LLD.md](file:///d:/Mini-proj/dashboard/docs/intial_LLD.md)  
> **Live Website Inspected**: `http://115.243.209.84/people_app/fertilizer/stock/tm/20/2020`

---

## Verdict: Good Foundation, But 5 Critical Assumptions Are Wrong

The LLD shows solid engineering thinking — layered scraping, normalized DB schema, checkpointing, rate limiting — all good. But **the design is built on assumptions about the website that don't match reality**. I verified this by actually visiting the site. Here's what breaks.

---

## 🚨 Critical Pain Points (Must Fix Before Coding)

### 1. The URL Drill-Down Model Is Wrong

> [!CAUTION]
> **LLD assumes**: GET-based URL patterns like `/stock/tm/{district_code}/{block_code}/`  
> **Reality**: The site uses **POST-based form submissions**, not GET URL navigation.

What actually happens:
- The entry page has **two dropdowns**: District (`மாவட்டம்`) and Block (`வட்டம்`)
- Selecting a District fires an **AJAX POST** to `/Fertilizer/getBlocks/{district_id}` to populate the Block dropdown
- Clicking "Search" (`தேடுக`) fires a **POST** to `/people_app/Fertilizer/result/tm`
- There is **no URL-based hierarchy** to crawl

**Impact**: Your entire `url_builder.py` and the 3-level GET-based scraping strategy won't work. You need a POST request workflow instead.

**Fix**: Replace URL-based navigation with:
```python
# Step 1: GET the main page to extract district IDs from the dropdown
# Step 2: For each district, POST to getBlocks/{district_id} to get block IDs  
# Step 3: For each (district, block) pair, POST to Fertilizer/result/tm with form data
```

---

### 2. Data Is In Cards, Not Flat HTML Tables

> [!CAUTION]
> **LLD assumes**: Single `<table>` with rows of dealers  
> **Reality**: Results are a **card-based grid layout** — each dealer is a separate card with an embedded mini-table

Each card contains:
- **Header**: Dealer name + code (e.g., `தத்தூர் தொடக்க வேளாண்மை கூட்டுறவு கடன் சங்கம் (999210)`)  
- **Address**: Location text below header
- **Stock mini-table**: Variable columns per dealer (some show 2 fertilizers, others 4+)
- **Contact**: Mobile number with Call button
- **Unit note**: `* அளவு கிலோவில்` (quantities in KG)

**Impact**: Your `TableParser.parse_dealer_stock_table()` logic of iterating `tr` rows in a single table is invalid. Each card needs individual parsing.

**Fix**: Parse cards individually:
```python
# Find all dealer cards (likely div.card or similar container)
# For each card:
#   - Extract dealer name + code from header
#   - Extract address from sub-header
#   - Parse the inner mini-table for fertilizer stocks
#   - Extract contact info
```

---

### 3. Fertilizer Column Names Are Dynamic and In Tamil

> [!WARNING]
> **LLD assumes**: Fixed column mapping like `cols[3] = Urea, cols[4] = DAP`  
> **Reality**: Each dealer's table has **different fertilizer columns** depending on what they stock. Column headers are in **Tamil** (e.g., `டி ஏ பி` for DAP, `பொட்டாஸ்` for Potash).

**Impact**: Hardcoded column indices will break across dealers. You also need a Tamil → English name mapping dictionary.

**Fix**:
1. Parse headers dynamically from each card's table
2. Create a robust Tamil-English fertilizer name mapping:
```python
FERTILIZER_MAP = {
    'யூரியா': 'Urea',
    'டி ஏ பி': 'DAP', 
    'பொட்டாஸ்': 'Potash/MOP',
    '16:16:16': '16-16-16',
    # ... discover all names from the actual data
}
```

---

### 4. Session/Cookie Management Is Missing

> [!WARNING]
> **LLD mentions session reuse** in scraper rules but doesn't design for it.  
> **Reality**: The site uses jQuery + AngularJS, and the form workflow requires maintaining a session (CSRF tokens, cookies) between requests.

**Impact**: Stateless `requests.get()` calls will fail. The search form likely validates that you came from the main page.

**Fix**: Use `requests.Session()` throughout:
```python
session = requests.Session()
# 1. GET main page (establishes cookies, gets CSRF token if any)
# 2. Use same session for all subsequent POST requests
```

---

### 5. `requests` + `BeautifulSoup` May Be Insufficient

> [!IMPORTANT]
> The page uses AngularJS and jQuery for dynamic content loading. The block dropdown is populated via AJAX after district selection. This means some content may require JavaScript execution.

**Recommendation**: 
- **Try `requests` first** (the POST endpoints might return full HTML without needing JS)
- **Have Playwright/Selenium as a fallback** if the POST approach doesn't return complete data
- Document this decision in your reconnaissance phase

---

## ⚠️ Moderate Pain Points (Design Gaps)

### 6. No `fertilizers` Master Table

Your `fertilizer_stock` table stores `fertilizer_name` as a free-text VARCHAR. Over time, inconsistent naming will creep in (e.g., "DAP" vs "D.A.P" vs "டி ஏ பி").

**Fix**: Add a `fertilizers` reference table:
```sql
CREATE TABLE fertilizers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 'DAP', 'UREA'
    name_en VARCHAR(100),                   -- 'Di-Ammonium Phosphate'
    name_ta VARCHAR(100),                   -- 'டி ஏ பி'
    category VARCHAR(50)                    -- 'Phosphatic', 'Nitrogenous'
);
```
Then `fertilizer_stock.fertilizer_name` → `fertilizer_stock.fertilizer_id` (FK to `fertilizers`).

### 7. Dealer Dedup Strategy Is Fragile

Using `UNIQUE(license_no)` for dealer deduplication is risky:
- What if license numbers aren't on the results page? (I didn't see them in the card layout)
- What if the same dealer appears with slightly different names across blocks?

**Fix**: Use a composite key `UNIQUE(dealer_code, block_id)` where `dealer_code` is the ID in parentheses from the card header (e.g., `999210`).

### 8. No Concurrency / Parallelism Strategy

Your LLD mentions `time.sleep(2)` for rate limiting but the pipeline is purely sequential. With ~38 districts × ~15 blocks = ~570 requests at 2s each = **~19 minutes minimum**.

**Recommendation**: Add an `asyncio` + `aiohttp` option with a configurable concurrency limit (e.g., 3 concurrent requests). This cuts scrape time to ~6 minutes while still being respectful.

### 9. Missing Error Granularity

The orchestrator has a single `try/except` around the entire run. If district #20 fails, you lose progress on districts 1-19.

**Fix**: Error handling per district/block:
```python
for district in districts:
    try:
        # scrape blocks for this district
    except Exception as e:
        log.error(f"Failed district {district['name']}: {e}")
        failed_districts.append(district)
        continue  # don't stop the whole run
```

### 10. Checkpoint File Missing From Design

The LLD mentions "CHECKPOINTING — Save progress" but doesn't design it. You need:
- A checkpoint file/table that records: last successfully scraped `(district_code, block_code)`
- On resume, skip already-scraped combinations for the current date

---

## ✅ What's Good in the LLD

| Aspect | Assessment |
|---|---|
| Folder structure | Clean, well-organized separation of concerns |
| DB schema design | Normalized, time-series ready, good indexes |
| Scraping rules | Rate limiting, retry, timeout all correct |
| Test plan | Comprehensive — unit, integration, spot-check, failure |
| Golden Rule approach | "One end-to-end first, then scale" is exactly right |
| Orchestrator pattern | Clean pipeline → good for maintainability |

---

## 📋 Recommended Next Steps

1. **Do real reconnaissance first** — Save sample HTML from the POST responses, not just view the page. Inspect the actual response body from `/Fertilizer/result/tm`
2. **Map all district IDs** — Extract the full dropdown `<option>` list from the main page
3. **Map all fertilizer names** — Collect every Tamil fertilizer name that appears in results, build the mapping dictionary
4. **Prototype the POST workflow** — Write a 20-line script that does: GET main page → POST for blocks → POST for results → print parsed cards
5. **Update the LLD** with the corrected data flow before writing production code

---

## 🎬 Website Inspection Recording

![Browser inspection of the target fertilizer website](C:\Users\FAI-Sathish\.gemini\antigravity\brain\bb5e4e6f-280b-4513-9d5e-7e9c35475f8d\website_inspection_1774525592669.webp)
