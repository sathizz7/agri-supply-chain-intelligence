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
│     │  --section fertilizer  --subsection price  --check-health     │
│     │  --resume (reuse last incomplete run_id for checkpoint cont.) │
│     ▼                                                               │
│   Orchestrator                                                      │
│     │  creates ScrapeRun, runs controller, validates results        │
│     │                                                               │
│     └── FertilizerController                                        │
│           ├── StockPositionParser   ✅ (ng-init JSON, session-based)│
│           ├── FertilizerPriceParser ✅ (JSON API, stateless)        │
│           └── BiofertilizerParser   🔮 (future — REST/Playwright)   │
│                                                                     │
│   Utilities (core/)                                                 │
│     ├── http_utils.py   — retry decorator, rate-limit, headers      │
│     └── metadata.py     — "Last update date" parsing                │
│                                                                     │
│   Database (database/)                                              │
│     ├── Alembic migrations                                          │
│     ├── ORM models (normalized relational)                          │
│     └── Operations (upsert helpers)                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Design Principles

- **No premature abstraction** — no registry, no ABCs. Extract patterns when a second section proves duplication
- **Each parser owns its HTTP** — StockPosition keeps `requests.Session()`, Price uses stateless `requests.post()` with `retry_request()`
- **No legacy parallel paths** — old `scraper/` and `parser/` directories are migrated and deleted
- **Validation is mandatory** — every parser has fetch → parse → validate → persist
- **`safe_parse_number` returns `None`** — callers decide whether unknown means 0 or NULL. No silent 0.0 for garbage.
- **Bilingual** — English default (`/en/` URLs), Tamil preserved in `name_ta` columns
- **Error isolation** — one parser failure never kills others

## Key Facts (from live site inspection)

- Main dashboard: `https://www.tnagrisnet.tn.gov.in/people_app/dashboard/main/en`
- Fertilizer index: `http://115.243.209.84/people_app/fertilizer/index/en/20/2020`
- Site uses **POST-based form workflow** (NOT GET URL crawling)
- AngularJS + jQuery frontend — data often embedded via ng-init JSON
- Requires `requests.Session()` for stock position (cookie persistence)
- Price endpoint is stateless — no session needed
- "Last update date" available on stock page (span.text-danger)

## Sections & Endpoints

### Section: Fertilizer

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

**Price endpoints:**
| Purpose | Method | URL |
|---------|--------|-----|
| Entry page (product list) | GET | `/people_app/fertilizer_price/index/en/20/2020` |
| Get prices for product | POST | `/people_app/fertilizer_price/fertDetails/{fert_id}` |

## Folder Structure

```
d:\Mini-proj\dashboard\
├── CLAUDE.md                          # This file — system design brain
├── main.py                            # CLI entry point
├── requirements.txt
├── alembic.ini                        # Alembic configuration
├── alembic/                           # Migration scripts
│   ├── env.py
│   └── versions/
├── .env / .env.example
│
├── tfais/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # DB URL, section URLs, timeouts
│   │
│   ├── core/                          # Thin shared utilities only
│   │   ├── __init__.py
│   │   ├── http_utils.py             # retry decorator, rate_limit(), DEFAULT_HEADERS
│   │   └── metadata.py              # MetadataExtractor (last-update-date)
│   │
│   ├── sections/                      # Section-wise scraper modules
│   │   ├── __init__.py
│   │   └── fertilizer/
│   │       ├── __init__.py
│   │       ├── controller.py          # FertilizerController (runs parsers directly)
│   │       └── parsers/
│   │           ├── __init__.py
│   │           ├── stock_position.py  # StockPositionParser (owns session, parsing, checkpoints)
│   │           ├── fertilizer_price.py# FertilizerPriceParser (stateless POST)
│   │           └── biofertilizer.py   # BiofertilizerParser (stub)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── models.py                  # All ORM models
│   │   └── operations.py             # Upsert helpers
│   │
│   └── pipeline/
│       ├── __init__.py
│       └── orchestrator.py            # Orchestrator (section-aware)
│
├── dashboard/
│   └── app.py                         # Streamlit dashboard
├── docs/
│   ├── modular_HLD.md                 # Authoritative architecture doc
│   ├── subsection_parser_logic.md    # Parser specs per subsection
│   └── (legacy docs archived)
├── tests/
│   ├── test_stock_position.py
│   ├── test_fertilizer_price.py
│   └── test_db.py
└── logs/
    └── .gitkeep
```

> **Note:** The legacy `scraper/` and `parser/` directories are deleted. All logic lives in `sections/fertilizer/parsers/`.

## Database Schema

### Core Tables

| Table | Key Columns |
|-------|-------------|
| `districts` | `id`, `code UNIQUE`, `name_ta`, `name_en` |
| `blocks` | `id`, `code`, `name_ta`, `name_en`, `district_id FK`, `UNIQUE(code, district_id)` |
| `dealers` | `id`, `dealer_code`, `name_ta`, `address`, `contact`, `block_id FK` |
| `fertilizer_stock` | `id`, `dealer_id FK`, `fertilizer_name`, `quantity`, `unit`, `scrape_date`, `scrape_run_id` |
| `fertilizer_prices` | `id`, `product_id`, `product_name`, `company`, `price_per_50kg`, `scrape_date`, `scrape_run_id` |
| `biofertilizer_stock` | `id`, `district_code`, `district_name`, `product_name`, `quantity`, `unit`, `scrape_date`, `scrape_run_id` |
| `scrape_runs` | `id`, `started_at`, `status`, `section_id`, `subsection_id`, `source_updated_at` |
| `scrape_anomalies` | `id`, `scrape_run_id FK`, `parser_id`, `anomaly_type`, `detail`, `severity` |
| `scrape_checkpoints` | `id`, `run_id`, `parser_id`, `work_unit_key`, `status` |
| `section_metadata` | `id`, `section_id`, `subsection_id`, `source_updated_at`, `last_scraped_at` |

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

# Resume crashed run (reuse last incomplete run_id, skip done checkpoints)
python main.py --section fertilizer --resume

# Health check (monitoring)
python main.py --check-health

# Utilities
python main.py --list-districts
python main.py --create-tables

# Legacy compat
python main.py --district 3317 3338
```

## Validation & Monitoring

### Per-parser validation (fetch → parse → **validate** → persist)

| Level | Check | Action |
|---|---|---|
| Page | District returns 0 dealers but had dealers before | Flag ERROR, not EMPTY |
| Record | Price negative or >PRICE_SPIKE_MULTIPLIER × median | Log WARNING, persist, write to `scrape_anomalies` |
| Record | `safe_parse_number` returns too many `None`s (>MAX_NULL_RATIO) | Flag data quality issue |
| Run | Total count < COUNT_DROP_THRESHOLD of previous run | Mark `suspicious`, write to `scrape_anomalies` |

### Health check (`--check-health`)

Reports:
- Last successful run per subsection
- Days since last data update
- Record count trend (this run vs last 3 runs)
- Warnings for stale or anomalous data

## Rules

- **Each parser owns its HTTP** — no shared HttpClient class
- **All HTTP calls use `retry_request()`** — no bare `requests.post()` without retry
- **Per-parser error isolation** — one subsection failure never kills others
- **Per-parser checkpoints** — each parser defines its own work unit key
- **Validation thresholds are parser-level constants** — `COUNT_DROP_THRESHOLD`, `PRICE_SPIKE_MULTIPLIER`, `MAX_NULL_RATIO`. No magic numbers in methods.
- **`safe_parse_number()` returns `None` for garbage** — caller decides: `or 0.0` for stock (zero is valid), keep `None` for price (unknown ≠ zero)
- **Anomalies stored in `scrape_anomalies` table** — structured, queryable. Not a TEXT column.
- **Dedup key for dealers**: `UNIQUE(dealer_code, block_id)`
- **English as default language** — use `/en/` URLs
- **Bilingual storage** — `name_ta` + `name_en` for geography entities
- **Rate limit**: 2s (stock), 1s (price) — configurable via `settings.py`
- **Alembic for migrations** — always
- **Validation before persist** — always

## Known Constraints

- **Sequential execution only**: Both parsers iterate with `time.sleep()` between calls. Stock Position does ~570 requests at 2s each (~19 min). If parallelism is needed later, the "parser owns timing" pattern must be refactored into async-compatible design (`asyncio`/`aiohttp` or thread pool with shared rate limiter). Accepted trade-off: simplicity now, harder to parallelize later.

## Critical Design Docs

- [docs/modular_HLD.md](docs/modular_HLD.md) — **Authoritative architecture**
- [docs/subsection_parser_logic.md](docs/subsection_parser_logic.md) — **Per-subsection parser specs**

## Verification Commands

```bash
# Run all tests
pytest tests/ -v

# Pipeline (specific subsection)
python main.py --section fertilizer --subsection price

# Health check
python main.py --check-health

# Alembic migration
alembic upgrade head
alembic revision --autogenerate -m "description"
```
