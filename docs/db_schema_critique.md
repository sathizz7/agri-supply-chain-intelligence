# 🗄️ Senior Backend Critique: TFAIS Database Schema

> **Reviewer Perspective**: Backend Developer, 10+ years production experience  
> **Schema Reviewed**: 7 tables from [CLAUDE.md](file:///d:/Mini-proj/dashboard/CLAUDE.md) and [revised_HLD.md](file:///d:/Mini-proj/dashboard/docs/revised_HLD.md)

---

## Your Question: 1 Table or Many Tables?

**Short answer**: **Multiple tables is the correct production approach for your use case. But you have _one too many_ tables.**

Let me explain why with concrete reasoning, then critique each table.

---

## The Single-Table vs Multi-Table Decision

### What a single "flat" table would look like

If you stored everything in one table:

```sql
CREATE TABLE fertilizer_data (
    id              SERIAL PRIMARY KEY,
    district_code   VARCHAR(10),
    district_name   VARCHAR(100),
    block_code      VARCHAR(10),
    block_name      VARCHAR(100),
    dealer_code     VARCHAR(20),
    dealer_name     VARCHAR(200),
    dealer_address  TEXT,
    dealer_contact  VARCHAR(20),
    fertilizer_name VARCHAR(100),
    quantity_kg     DECIMAL(10,2),
    scrape_date     DATE,
    scraped_at      TIMESTAMP
);
```

One row per (dealer × fertilizer × day). For 38 districts × 15 blocks × 20 dealers × 8 fertilizers = **~91,200 rows per daily scrape**.

### When single-table works (and when it doesn't)

| Factor | Single Table | Multiple Tables | Your Case |
|---|---|---|---|
| **Read speed** (simple queries) | ✅ Faster — no JOINs | ❌ Needs JOINs | You need both |
| **Read speed** (aggregations) | ❌ Scans huge text columns | ✅ Joins on small integer FKs | Dashboard needs aggregations |
| **Write speed** | ✅ Single insert | ❌ Multiple upserts | Scraper runs 1x/day, write speed irrelevant |
| **Storage** | ❌ Duplicate strings everywhere | ✅ Normalized, compact | "அரியலூர்" repeated 91K times vs once |
| **Data integrity** | ❌ Typos go undetected | ✅ FK constraints catch bad data | Critical for daily scraping |
| **Schema evolution** | ❌ ALTER TABLE on huge table | ✅ Change only affected table | You'll definitely add columns |
| **Update anomalies** | ❌ Dealer changes contact → update 8+ rows | ✅ Update 1 row in `dealers` | Dealers change contact/address |
| **Complexity** | ✅ Simple mental model | ❌ More code to write | You're learning, simplicity matters |

### The verdict for TFAIS

**Multiple tables is the right choice because**:

1. **Daily scraping creates massive duplication** — "அரியலூர்" (district name) would be repeated ~2,400 times per day in a flat table vs stored once in `districts`.

2. **Your dashboard needs aggregations** — "Total DAP stock in Thanjavur district" requires grouping across hundreds of rows. With normalized tables, this is a fast JOIN on integer IDs. With a flat table, it's string comparison on repeated text.

3. **Data changes independently** — A dealer might change their phone number, but their stock data from last week should keep the old contact info in its scrape record. Normalization separates "what changes" from "what's historical".

4. **Deduplication is critical** — Your scraper runs daily. UNIQUE constraints on separate tables prevent the same district being inserted 365 times/year. In a flat table, you'd need application-level dedup.

---

## But — You have ONE table too many

### The `fertilizers` master table is over-engineering for your current scope

Your schema has:

```
fertilizers (master)  →  fertilizer_stock (fact)
     id, code, name_ta, name_en      fertilizer_id (FK)
```

**Why this is premature**:

1. You decided to **extract text as-is** (no Tamil→English translation). So `name_en` in the fertilizers table adds no value right now.

2. The fertilizer names come directly from HTML headers. They're already the natural key. Forcing an FK lookup adds complexity to every insert:
   ```python
   # WITH fertilizers master table (current design):
   fert_id = db.get_or_create_fertilizer(header_name)  # extra query per cell
   db.insert_stock(dealer_id, fert_id, quantity, ...)
   
   # WITHOUT fertilizers table (simpler):
   db.insert_stock(dealer_id, header_name, quantity, ...)  # direct insert
   ```

3. There are only ~8-15 unique fertilizer types. The "naming drift" risk (`DAP` vs `D.A.P`) is real but manageable with a simple validation set in code, not a whole database table.

### My recommendation

**For MVP**: Drop the `fertilizers` master table. Store `fertilizer_name VARCHAR(100)` directly on `fertilizer_stock`. Add a CHECK constraint or application-level validation for known names.

**Later (when you need it)**: Add the `fertilizers` master table when you actually build the English dashboard or need categorization (Nitrogenous/Phosphatic). This is a 30-minute migration.

---

## Table-by-Table Critique

### 1. `districts` — ✅ Good

```
| id | code UNIQUE | name_ta | name_en | created_at |
```

**Positives**:
- `code UNIQUE` — correct, prevents duplicate districts
- Separate `name_ta` — right for Tamil source data

**Issues**:
- `name_en` — you said no translation. Drop this column for MVP, or keep it nullable for later.

---

### 2. `blocks` — ✅ Good

```
| id | code | name_ta | district_id FK | UNIQUE(code, district_id) | created_at |
```

**Positives**:
- Composite unique `(code, district_id)` — correct! Block codes may repeat across districts.

**Issues**:
- Same `name_en` comment as districts.

---

### 3. `dealers` — ⚠️ Has Issues

```
| id | dealer_code | name_ta | address | contact | block_id FK | UNIQUE(dealer_code, block_id) |
```

**Positives**:
- `UNIQUE(dealer_code, block_id)` — correct dedup strategy using the card header code.

**Issues**:

**Issue 3a: What if `dealer_code` is empty?**

Your card parser has: `code_match = re.search(r'\((\d{4,})\)', text)`. If this regex doesn't match, `dealer_code` is `''`. Now you have `UNIQUE('', block_id)` — and the second dealer without a code in the same block will violate the constraint.

**Fix**: Make the UNIQUE constraint a partial index, or generate a synthetic code:
```sql
-- Option A: Allow multiple empty codes
CREATE UNIQUE INDEX idx_dealer_dedup 
ON dealers(dealer_code, block_id) 
WHERE dealer_code != '';

-- Option B: Composite name+block fallback
UNIQUE(COALESCE(NULLIF(dealer_code, ''), name_ta), block_id)
```

**Issue 3b: Missing `updated_at`**

The HLD mentions `updated_at` on dealers, but CLAUDE.md doesn't list it. Dealer contact/address can change between scrapes. Without `updated_at`, you can't tell if a dealer's info is fresh or stale.

**Fix**: Add `updated_at TIMESTAMP DEFAULT NOW()` and update it on every upsert.

---

### 4. `fertilizers` — ⚠️ Drop for MVP (see above)

If you keep it later, the design is fine. But for now, it adds query overhead without benefit since you're extracting text as-is.

---

### 5. `fertilizer_stock` — 🔴 Has Critical Issues

```
| id | dealer_id FK | fertilizer_id FK | quantity_kg | scraped_at | scrape_run_id |
```

This is your **fact table** — the most important one. It needs the most scrutiny.

**Issue 5a: `scraped_at` vs `scrape_date` confusion**

CLAUDE.md says `scraped_at` (timestamp). The HLD says `scrape_date` (DATE). These are different:
- `scrape_date DATE` — the logical date this data represents (correct for UNIQUE constraint)
- `scraped_at TIMESTAMP` — when the row was created (metadata)

**You need BOTH**:
```sql
scrape_date  DATE NOT NULL,        -- "the data is for this date"
created_at   TIMESTAMP DEFAULT NOW() -- "we scraped it at this time"
```

The UNIQUE constraint should be on `(dealer_id, fertilizer_name, scrape_date)` — one stock reading per dealer per fertilizer per day.

**Issue 5b:  `quantity_kg` — is it actually KG?**

The website note says `* அளவு கிலோவில்` (quantities in KG). But do you know for sure? Some fertilizers might be in "bags" (50kg each). If you blindly store '1650' as KG when it means '1650 bags = 82,500 KG', your dashboard aggregations will be wildly wrong.

**Fix**: Add a `unit VARCHAR(10) DEFAULT 'KG'` column. Even if everything is KG today, this prepares for the case where it changes.

**Issue 5c: No index for the most common dashboard query**

Your dashboard's #1 query will be: _"Show me stock for district X on date Y"_

```sql
SELECT d.name_ta, dl.name_ta, fs.fertilizer_name, fs.quantity_kg
FROM fertilizer_stock fs
JOIN dealers dl ON fs.dealer_id = dl.id
JOIN blocks b ON dl.block_id = b.id
WHERE b.district_id = ? AND fs.scrape_date = ?
```

This needs a composite index:
```sql
CREATE INDEX idx_stock_date_dealer ON fertilizer_stock(scrape_date, dealer_id);
```

The HLD has `idx_stock_date` and `idx_stock_dealer` separately, but a **composite index** is what the query planner actually needs.

---

### 6. `scrape_metadata` / `scrape_runs` — ✅ Good

```
| id | started_at | completed_at | status | counts... |
```

**Positives**:
- Tracks every scrape run — essential for debugging.
- `status` with running/success/partial/failed — the `partial` state is a nice touch that most people forget.

**Issue**: No `trigger_type` column. Was this run triggered by scheduler, manual, or resume? Helps debugging when runs overlap.

```sql
trigger_type  VARCHAR(20) DEFAULT 'manual'  -- manual/scheduled/resume
```

---

### 7. `scrape_checkpoints` — ✅ Good Design

```
| id | run_id | district_code | block_code | status | dealers_found | completed_at |
```

**Positives**:
- Enables resume-on-failure — this is production-quality thinking.
- Storing `dealers_found` per checkpoint — great for sanity checks.

**Issue**: Using `district_code` and `block_code` (strings) instead of `district_id` and `block_id` (integer FKs).

**Why this is actually fine**: Checkpoints are written during scraping, before districts/blocks may be committed to the DB. Using codes (which come from the website) avoids a chicken-and-egg problem. Good call.

---

## Recommended Final Schema

Based on all the above, here's the schema I'd recommend for MVP:

```sql
-- ===== ENTITY TABLES (normalized, separate) =====

CREATE TABLE districts (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(10) UNIQUE NOT NULL,
    name_ta     VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE blocks (
    id            SERIAL PRIMARY KEY,
    code          VARCHAR(10) NOT NULL,
    name_ta       VARCHAR(100) NOT NULL,
    district_id   INTEGER NOT NULL REFERENCES districts(id),
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(code, district_id)
);

CREATE TABLE dealers (
    id            SERIAL PRIMARY KEY,
    dealer_code   VARCHAR(20) NOT NULL DEFAULT '',
    name_ta       VARCHAR(200) NOT NULL,
    address       TEXT,
    contact       VARCHAR(20),
    block_id      INTEGER NOT NULL REFERENCES blocks(id),
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);
-- Partial unique: only enforce uniqueness when dealer_code is non-empty
CREATE UNIQUE INDEX idx_dealer_dedup 
ON dealers(dealer_code, block_id) WHERE dealer_code != '';

-- ===== FACT TABLE (the core data) =====

CREATE TABLE fertilizer_stock (
    id              SERIAL PRIMARY KEY,
    dealer_id       INTEGER NOT NULL REFERENCES dealers(id),
    fertilizer_name VARCHAR(100) NOT NULL,     -- stored AS-IS from card headers
    quantity        DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit            VARCHAR(10) DEFAULT 'KG',
    scrape_date     DATE NOT NULL,             -- logical date
    scrape_run_id   INTEGER REFERENCES scrape_runs(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(dealer_id, fertilizer_name, scrape_date)
);

-- ===== OPERATIONAL TABLES =====

CREATE TABLE scrape_runs (
    id              SERIAL PRIMARY KEY,
    started_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP,
    status          VARCHAR(20) DEFAULT 'running',
    trigger_type    VARCHAR(20) DEFAULT 'manual',
    total_districts INTEGER DEFAULT 0,
    total_blocks    INTEGER DEFAULT 0,
    total_dealers   INTEGER DEFAULT 0,
    total_stocks    INTEGER DEFAULT 0,
    failed_blocks   INTEGER DEFAULT 0,
    error_log       TEXT
);

CREATE TABLE scrape_checkpoints (
    id             SERIAL PRIMARY KEY,
    scrape_run_id  INTEGER NOT NULL REFERENCES scrape_runs(id),
    district_code  VARCHAR(10) NOT NULL,
    block_code     VARCHAR(10) NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending',
    dealers_found  INTEGER DEFAULT 0,
    error_message  TEXT,
    completed_at   TIMESTAMP,
    UNIQUE(scrape_run_id, district_code, block_code)
);

-- ===== INDEXES (tuned for dashboard queries) =====

CREATE INDEX idx_stock_date_dealer 
ON fertilizer_stock(scrape_date, dealer_id);  -- composite for dashboard

CREATE INDEX idx_stock_fertilizer 
ON fertilizer_stock(fertilizer_name);         -- filter by fertilizer type

CREATE INDEX idx_blocks_district 
ON blocks(district_id);                       -- join performance

CREATE INDEX idx_dealers_block 
ON dealers(block_id);                         -- join performance

CREATE INDEX idx_checkpoint_run 
ON scrape_checkpoints(scrape_run_id, status); -- checkpoint lookups
```

**Tables: 6 (not 7)** — dropped `fertilizers` master table for MVP.

---

## Scorecard

| Table | Verdict | Score |
|---|---|---|
| `districts` | Good, drop `name_en` for MVP | 8/10 |
| `blocks` | Good, correct composite unique | 9/10 |
| `dealers` | Fix empty `dealer_code` dedup, add `updated_at` | 6/10 |
| `fertilizers` | Drop for MVP — over-engineering without Tamil→English | 4/10 |
| `fertilizer_stock` | Fix `scraped_at`/`scrape_date` split, add `unit`, fix indexes | 5/10 |
| `scrape_runs` | Good, add `trigger_type` | 8/10 |
| `scrape_checkpoints` | Good design, strings-for-codes is pragmatic | 9/10 |

**Overall: 7/10** — Correct normalized approach, needs production hardening on the fact table.
