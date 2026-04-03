# TFAIS — Claude Code Guide

## Project

Tamil Nadu Fertilizer & Agricultural Intelligence System.
Modular scraper pipeline: scrapes multiple data sections from TN government portals → PostgreSQL → FastAPI → Streamlit dashboard.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TFAIS PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   CLI (main.py)                                                     │
│     │  --section fertilizer/seed/machinery                          │
│     │  --subsection price/agri/horti/season/tractor/women_plf/drone │
│     │  --district <code>  --resume  --check-health                  │
│     ▼                                                               │
│   Orchestrator                                                      │
│     │  creates ScrapeRun, runs controller, validates results        │
│     │                                                               │
│     ├── FertilizerController                                        │
│     │     ├── StockPositionParser   ✅ (ng-init JSON, session-based)│
│     │     ├── FertilizerPriceParser ✅ (JSON API, stateless)        │
│     │     └── BiofertilizerParser   🔮 (future)                     │
│     │                                                               │
│     ├── SeedController                                              │
│     │     ├── AgriSeedParser    ✅ (ng-init HTML, session-based)    │
│     │     ├── HortiSeedParser   ✅ (ng-init HTML, session-based)    │
│     │     └── SeasonSeedParser  ✅ (ng-init HTML, session-based)    │
│     │                                                               │
│     └── MachineryController                                         │
│           ├── PrivateTractorParser  ✅ (stateless GET JSON)         │
│           ├── WomenPLFParser        ✅ (stateless GET JSON)         │
│           └── DroneOwnersParser     ✅ (stateless GET JSON)         │
│                                                                     │
│   Utilities (core/)                                                 │
│     ├── http_utils.py   — retry decorator, rate-limit, headers      │
│     └── metadata.py     — "Last update date" parsing                │
│                                                                     │
│   Database (database/)                                              │
│     ├── Alembic migrations                                          │
│     ├── ORM models (normalized relational, multi-schema)            │
│     └── Operations (upsert helpers, one function per table)         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Design Principles

- **No premature abstraction** — no registry, no ABCs. Extract patterns when a second section proves duplication
- **Each parser owns its HTTP** — seed/fertilizer use `requests.Session()`, machinery uses stateless GET
- **No legacy parallel paths** — old `scraper/` and `parser/` directories are deleted
- **Validation is mandatory** — every parser has fetch → parse → validate → persist
- **`safe_parse_number` returns `None`** — callers decide whether unknown means 0 or NULL
- **Bilingual** — English default (`/en/` URLs), Tamil preserved in `name_ta` columns
- **Error isolation** — one parser failure never kills others
- **One table per subsection** — no discriminator columns (no `source_type`). Machinery and seed both follow this pattern
- **`seen = set()` + `no_autoflush`** — all batch inserts use in-memory dedup to prevent UniqueViolation on same-batch duplicates

## Key Facts (from live site inspection)

- Main dashboard: `https://www.tnagrisnet.tn.gov.in/people_app/dashboard/main/en`
- Fertilizer index: `http://115.243.209.84/people_app/fertilizer/index/en/20/2020`
- **Seed portal district codes are different from fertilizer codes** — seed uses short integers (e.g. `30`=Ariyalur, `23`=Theni, `11`=Coimbatore). Fertilizer uses 4-digit codes (e.g. `3338`).
- Site uses **POST-based form workflow** for fertilizer/seed (NOT GET URL crawling)
- Machinery CHC portal uses **stateless GET JSON** — no session, no CSRF
- AngularJS + jQuery frontend — seed/fertilizer data embedded via ng-init JSON
- Requires `requests.Session()` for seed and fertilizer stock (cookie/CSRF persistence)

## Sections & Endpoints

### Section: Fertilizer (`base_url = http://115.243.209.84/people_app`)

| Subsection | Status | Method | URL | Response |
|---|---|---|---|---|
| Stock Position | ✅ Done | POST | `/Fertilizer/result/en` | HTML with ng-init JSON |
| Price | ✅ Done | POST | `/fertilizer_price/fertDetails/{fert_id}` | JSON array |
| Biofertilizer | 🔮 Future | REST API | `tnagrisnet.tn.gov.in/agri_api/uatt/fert/*` | JSON (Angular SPA) |

**Stock Position endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Entry page (session + districts) | GET | `/people_app/fertilizer/stock/en/20/2020` |
| Get blocks for district | POST | `/people_app/Fertilizer/getBlocks/{district_id}` |
| Get dealer results | POST | `/people_app/Fertilizer/result/en` |

### Section: Seed (`base_url = https://www.tnagrisnet.tn.gov.in/people_app`)

**IMPORTANT:** Seed district codes are portal-specific short integers, NOT the same as fertilizer district codes.

| Subsection | Status | Iteration | Entry URL |
|---|---|---|---|
| agri | ✅ Done | district → block → crop | `/Seed/seed_gov/en` |
| horti | ✅ Done | district → block → stock_type → stock | `/Horti_seed/index/en` |
| season | ✅ Done | district → block → season → crop | `/Season/index/en` |

**Agri endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Entry page (districts + crops) | GET | `/Seed/seed_gov/en` |
| Get blocks | POST | `/Seed/getBlocks/{district_id}` |
| Get results | POST | `/Seed/result/en` |

**Horti endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Entry page | GET | `/Horti_seed/index/en` |
| Get blocks | POST | `/Seed/getBlocks/{district_id}` (shared) |
| Get stock types | POST | `/Horti_seed/loadStockType/{block_id}` → `[{stock_type_id, stock_type_name}]` |
| Get stocks | POST | `/Horti_seed/loadStock/{stock_type_id}/{block_id}` → `[{stock_id, stock_name}]` |
| Get results | POST | `/Horti_seed/result/en` (fields: `district_id`, `block_id`, `stock_type_id`, `stock_id`) |

**Season endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Entry page (seasons hardcoded in `<select#season>`) | GET | `/Season/index/en` |
| Get blocks | POST | `/Seed/getBlocks/{district_id}` (shared) |
| Get crops per season | POST | `/Season/getCrop/{season}/{district_id}/{block_id}` → `[{stock_id, stock_name}]` |
| Get results | POST | `/Season/result/en` (fields: `district_id`, `block_id`, `season`, `crop_id`) |

**Seed result fields (all three subsections):**
`cropName`, `varietyName`, `className`, `full_name`, `user_phone`, `aecName`, `price`, `quantity`, `units`

### Section: Machinery (`base_url = http://115.243.209.84/chc/Mobile`)

| Subsection | Status | Iteration | Notes |
|---|---|---|---|
| tractor | ✅ Done | district → block → results | GET JSON, stateless |
| women_plf | ✅ Done | district → block → results | WDS-specific district/block endpoints |
| drone | ✅ Done | district → results | District-only loop, block embedded in record |

**Tractor endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Get districts | GET | `/getDistricts` |
| Get blocks | GET | `/getBlocks/{district_id}` |
| Get results | GET | `/getPrivateOwners/{block_id}` |

**Women PLF endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Get districts | GET | `/getWDSDistricts` |
| Get blocks | GET | `/getWDSBlocks/{district_id}` |
| Get results | GET | `/getWDCMechanics/{block_id}` |

**Drone endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Get districts | GET | `/getDistricts` |
| Get results | GET | `/loadDrone/{district_id}` |

## Folder Structure

```
d:\Mini-proj\dashboard\
├── CLAUDE.md                          # This file — system design brain
├── main.py                            # CLI entry point
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/                      # All migrations (run alembic upgrade head before scraping)
├── .env / .env.example
│
├── tfais/
│   ├── config/
│   │   └── settings.py               # DB URL, all section URLs, rate limits
│   │
│   ├── core/
│   │   ├── http_utils.py             # retry_request(), rate_limit(), DEFAULT_HEADERS
│   │   └── metadata.py              # safe_parse_number(), MetadataExtractor
│   │
│   ├── sections/
│   │   ├── fertilizer/
│   │   │   ├── controller.py
│   │   │   └── parsers/
│   │   │       ├── stock_position.py
│   │   │       ├── fertilizer_price.py
│   │   │       └── biofertilizer.py  # stub
│   │   │
│   │   ├── seed/
│   │   │   ├── controller.py
│   │   │   └── parsers/
│   │   │       ├── base_angular.py   # BaseAngularSeedParser (session, ng-init, checkpoints)
│   │   │       ├── agri_seed.py      # AgriSeedParser + AgriSeedRecord
│   │   │       ├── horti_seed.py     # HortiSeedParser + HortiSeedRecord
│   │   │       └── season_seed.py    # SeasonSeedParser + SeasonSeedRecord
│   │   │
│   │   └── machinery/
│   │       ├── controller.py
│   │       └── parsers/
│   │           ├── base_machinery.py # BaseMachineryParser (stateless GET JSON)
│   │           ├── tractor.py        # PrivateTractorParser + TractorRecord
│   │           ├── woman_mechanics.py# WomenPLFParser + WomenPLFRecord
│   │           └── drone.py          # DroneOwnersParser + DroneRecord
│   │
│   ├── database/
│   │   ├── connection.py             # search_path: public, fertilizer, seed, machinery
│   │   ├── models.py                 # All ORM models (multi-schema)
│   │   └── operations.py            # One insert function per table
│   │
│   └── pipeline/
│       └── orchestrator.py           # Section-aware orchestrator
│
├── dashboard/
│   └── app.py                        # Streamlit dashboard
├── docs/
└── logs/
```

## Database Schema

### Schema Layout

| PostgreSQL Schema | Tables |
|---|---|
| `public` | `districts`, `blocks`, `scrape_runs`, `scrape_checkpoints`, `scrape_anomalies`, `section_metadata` |
| `fertilizer` | `dealers`, `fertilizer_stock`, `fertilizer_prices` |
| `seed` | `agri_seeds`, `horti_seeds`, `season_seeds` |
| `machinery` | `tractor_owners`, `women_plf`, `drone_owners` |

Connection `search_path`: `public,fertilizer,seed,machinery`

### Seed Tables

#### `seed.agri_seeds`
| Column | Type | Source |
|---|---|---|
| `district_code`, `district_name` | String | Bootstrap `<select#district_id>` |
| `block_code`, `block_name` | String | `getBlocks` → `id`, `Block_Name` |
| `crop_name` | String | `cropName` |
| `crop_variety` | String | `varietyName` |
| `seed_class` | String | `className` |
| `agency_name` | String | `aecName` |
| `contact_person` | String | `full_name` |
| `contact_phone` | String | `user_phone` |
| `quantity_available` | Float | `quantity` |
| `unit` | String | `unit` (default "MT") |
| `price` | String | `price` |
| `scrape_date` | Date | run date |

Unique key: `(block_code, crop_name, crop_variety, agency_name, scrape_date)`

#### `seed.horti_seeds`
| Column | Type | Source |
|---|---|---|
| `stock_type` | String | `stock_type_name` from `loadStockType` |
| `input_name` | String | `cropName` from result |
| `crop_variety` | String | `varietyName` |
| `seed_class` | String | `className` |
| `agency_name` | String | `aecName` |
| `contact_person` | String | `full_name` |
| `contact_phone` | String | `user_phone` |
| `quantity_available` | Float | `quantity` |
| `unit` | String | `units` (default "Nos") |
| `price` | String | `price` |

Unique key: `(block_code, stock_type, input_name, agency_name, scrape_date)`

#### `seed.season_seeds`
| Column | Type | Source |
|---|---|---|
| `season` | String NOT NULL | season name string (e.g. "Kuruvai") |
| `crop_name` | String | `cropName` from result |
| `crop_variety` | String | `varietyName` |
| `seed_class` | String | `className` |
| `agency_name` | String | `aecName` |
| `contact_person` | String | `full_name` |
| `contact_phone` | String | `user_phone` |
| `quantity_available` | Float | `quantity` |
| `unit` | String | `unit` (default "MT") |
| `price` | String | `price` |

Unique key: `(block_code, season, crop_name, crop_variety, agency_name, scrape_date)`

### Machinery Tables

#### `machinery.tractor_owners`
Unique key: `(district_code, block_code, owner_name, machinery_name, scrape_date)`
Key fields: `maker_model`, `machinery_name`, `implement_name`, `mobile_number`

#### `machinery.women_plf`
Unique key: `(district_code, block_code, plf_name, scrape_date)`
Key fields: `plf_name`, `mobile_number` (← `PLF_President`), `contact_address`, `machinery_procured`, `available_count`, `panchayat`

#### `machinery.drone_owners`
Unique key: `(district_code, block_code, owner_name, scrape_date)`
Key fields: `block_code`, `block_name` (village from API), `owner_name` (← `ownerName`), `mobile_number`

### Core Tables (public schema)

| Table | Key Columns |
|-------|-------------|
| `districts` | `id`, `code UNIQUE`, `name_ta`, `name_en` |
| `blocks` | `id`, `code`, `name_ta`, `name_en`, `district_id FK` |
| `dealers` | `id`, `dealer_code`, `name_ta`, `address`, `contact`, `block_id FK` |
| `fertilizer_stock` | `dealer_id FK`, `fertilizer_name`, `quantity`, `unit`, `scrape_date` |
| `fertilizer_prices` | `product_id`, `product_name`, `company`, `price_per_50kg`, `scrape_date` |
| `scrape_runs` | `id`, `started_at`, `status`, `section_id`, `subsection_id` |
| `scrape_anomalies` | `scrape_run_id FK`, `parser_id`, `anomaly_type`, `detail`, `severity` |
| `scrape_checkpoints` | `run_id`, `parser_id`, `work_unit_key`, `status` |
| `section_metadata` | `section_id`, `subsection_id`, `source_updated_at`, `last_scraped_at` |

### Migration History

| Migration | Description |
|---|---|
| `87151021f090` | Baseline existing schema |
| `734a2e0f842d` | Add modular pipeline schema |
| `530819517819` | Finalize checkpoint schema |
| `bbe3617efcd2` | Rename name_ta columns |
| `77eae4d502b9` | Restore bilingual name columns |
| `c4e5d1f2a8b3` | Add seed_stocks table (old unified table) |
| `d3f7a2b1e9c4` | Schema segregation: fertilizer + seed schemas |
| `a1b2c3d4e5f6` | Add machinery schema + 3 tables |
| `b2c3d4e5f6a7` | Fix drone_owners schema (add block cols, remove drone_count) |
| `c3d4e5f6a7b8` | Rename woman_mechanics → women_plf |
| `e4f5a6b7c8d9` | Split seed_stocks → agri_seeds + horti_seeds + season_seeds |
| `f5a6b7c8d9e0` | Add seed_class, contact_person, contact_phone, price to seed tables |

### Migration Strategy

- **Alembic** for all schema changes — never `create_all_tables()` in production
- Additive migrations only
- `alembic upgrade head` before each pipeline run

## CLI Usage

```bash
# Full scrape (all sections)
python main.py

# Section-specific
python main.py --section fertilizer
python main.py --section fertilizer --subsection price
python main.py --section seed --subsection agri
python main.py --section seed --subsection horti
python main.py --section seed --subsection season
python main.py --section machinery --subsection tractor
python main.py --section machinery --subsection women_plf
python main.py --section machinery --subsection drone

# District filter — use section-appropriate codes
# Seed uses its own codes: 30=Ariyalur, 23=Theni, 11=Coimbatore, etc.
# Machinery/fertilizer use different 4-digit codes
python main.py --section seed --subsection agri --district 23
python main.py --section machinery --subsection tractor --district 30

# Resume crashed run
python main.py --section seed --resume

# Health check
python main.py --check-health

# Utilities
python main.py --list-districts
python main.py --create-tables
```

## Validation & Monitoring

### Per-parser validation (fetch → parse → **validate** → persist)

| Level | Check | Action |
|---|---|---|
| Page | District returns 0 dealers but had dealers before | Flag ERROR, not EMPTY |
| Record | Price negative or >PRICE_SPIKE_MULTIPLIER × median | Log WARNING, persist, write to `scrape_anomalies` |
| Record | `safe_parse_number` returns too many `None`s (>MAX_NULL_RATIO) | Flag data quality issue |
| Run | Total count < COUNT_DROP_THRESHOLD of previous run | Mark `suspicious`, write to `scrape_anomalies` |

## Rules

- **Each parser owns its HTTP** — no shared HttpClient class
- **All HTTP calls use `retry_request()`** — no bare `requests.post()` without retry
- **Per-parser error isolation** — one subsection failure never kills others
- **Per-parser checkpoints** — each parser defines its own work unit key
- **One table per subsection** — never use a `source_type` discriminator column
- **`seen = set()` + `session.no_autoflush`** — all batch inserts must use this pattern to prevent intra-batch UniqueViolation
- **`safe_parse_number()` returns `None` for garbage** — caller decides: `or 0.0` for stock, keep `None` for price
- **Anomalies stored in `scrape_anomalies` table** — structured, queryable
- **Upsert updates ALL fields** — `if existing:` block must update every mutable field, not just quantity
- **English as default language** — use `/en/` URLs
- **Rate limit**: 2s (seed/stock), 1s (price), 1s (machinery) — configurable via `settings.py`
- **Alembic for migrations** — always
- **Validation before persist** — always
- **District codes are section-specific** — seed portal uses its own integer codes, do not mix with fertilizer codes

## Known Constraints

- **Sequential execution only**: Parsers iterate with `time.sleep()` between calls. Seed agri does district→block→crop (many requests). If parallelism needed later, must refactor to `asyncio`/`aiohttp`.
- **Seed block `id` field used as POST param** — not `Block_Code` (3-letter string). `get_blocks()` normalizes `id` → `code`.
- **Horti district 30 (Ariyalur) has no stock** — test with district 23 (Theni) which has horti data.
- **Season crops are dynamic** — fetched per season+district+block via `getCrop/{season}/{district}/{block}`, not static from entry page.

## Verification Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Run all tests
pytest tests/ -v

# Test seed section (use seed district codes)
python main.py --section seed --subsection agri --district 23
python main.py --section seed --subsection horti --district 23
python main.py --section seed --subsection season --district 23

# Test machinery
python main.py --section machinery --subsection tractor --district 30
python main.py --section machinery --subsection women_plf --district 30
python main.py --section machinery --subsection drone --district 30

# Health check
python main.py --check-health

# New Alembic migration
alembic revision --autogenerate -m "description"
```
