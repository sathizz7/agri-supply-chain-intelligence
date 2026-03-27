    # TFAIS — Claude Code Guide

## Project

Tamil Nadu Fertilizer Availability Intelligence System.
Scrapes fertilizer stock data from Tamil Nadu government portal → PostgreSQL → FastAPI → Streamlit dashboard.

## Key Facts (from live site inspection)

- Site URL: `http://115.243.209.84/people_app/fertilizer/stock/tm/20/2020`
- Site uses **POST-based form workflow** (NOT GET URL crawling)
- Results page has **card-based layout** (per-dealer cards with embedded mini-tables)
- Fertilizer column headers are in **Tamil**, dynamic per dealer
- Requires `requests.Session()` for cookie/session persistence
- AngularJS + jQuery frontend — may need Playwright fallback if `requests` fails

## Endpoints (live site)

| Purpose | Method | URL |
|---------|--------|-----|
| Entry page (session bootstrap + district list) | GET | `/people_app/fertilizer/stock/tm/20/2020` |
| Get blocks for a district | POST | `/people_app/Fertilizer/getBlocks/{district_id}` |
| Get dealer results for a (district, block) | POST | `/people_app/Fertilizer/result/tm` |

## Folder Structure

```
d:\Mini-proj\dashboard\
├── CLAUDE.md
├── main.py                    # CLI entry point
├── requirements.txt
├── .env                       # DB credentials (not committed)
├── .env.example
├── tfais/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # DB URL, base URLs, timeouts, rate limits
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── session_manager.py # SessionManager class
│   │   └── scraper.py         # FertilizerScraper class
│   ├── parser/
│   │   ├── __init__.py
│   │   └── card_parser.py     # CardParser + DealerRecord dataclass
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── connection.py      # Engine + session factory
│   │   └── operations.py      # Upsert helpers
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── orchestrator.py    # End-to-end pipeline
│   └── api/
│       ├── __init__.py
│       └── main.py            # FastAPI app
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── tests/
│   ├── test_scraper.py
│   ├── test_parser.py
│   └── test_db.py
└── logs/
    └── .gitkeep
```

## Implementation Phases

| Phase | Module | Status |
|-------|--------|--------|
| 0 | `scraper/session_manager.py` — SessionManager | Pending |
| 1 | `scraper/scraper.py` — FertilizerScraper | Pending |
| 2 | `parser/card_parser.py` — CardParser + DealerRecord | Pending |
| 3 | `database/` — models, connection, operations | Pending |
| 4 | `pipeline/orchestrator.py` — Orchestrator | Pending |
| 5 | `api/main.py` — FastAPI endpoints | Pending |
| 6 | `dashboard/app.py` — Streamlit UI | Pending |

## Critical Design Docs

- [docs/revised_HLD.md](docs/revised_HLD.md) — **Authoritative architecture** (supersedes intial_LLD.md)
- [docs/card_parser.md](docs/card_parser.md) — **Authoritative card parser spec**
- [docs/lld_review.md](docs/lld_review.md) — 5 critical issues and their fixes

## Database Schema (target)

| Table | Key Columns |
|-------|-------------|
| `districts` | `id`, `code UNIQUE`, `name_ta`, `name_en` |
| `blocks` | `id`, `code`, `name_ta`, `district_id FK`, `UNIQUE(code, district_id)` |
| `dealers` | `id`, `dealer_code`, `name_ta`, `address`, `contact`, `block_id FK`, `UNIQUE(dealer_code, block_id)` |
| `fertilizers` | `id`, `code UNIQUE`, `name_ta`, `name_en`, `category` |
| `fertilizer_stock` | `id`, `dealer_id FK`, `fertilizer_id FK`, `quantity_kg`, `scraped_at`, `scrape_run_id` |
| `scrape_metadata` | `id (run_id)`, `started_at`, `completed_at`, `status`, counts |
| `scrape_checkpoints` | `id`, `run_id`, `district_code`, `block_code`, `status`, `completed_at` |

## Rules (enforced in all phases)

- **Always use `requests.Session()`** — never stateless `requests.get()`
- **Per-district/block error isolation** — `try/except` + `continue`, never kill the whole run
- **Dedup key**: `UNIQUE(dealer_code, block_id)` — NOT license number
- **Parser triage first**: classify page as `HAS_RESULTS | EMPTY | ERROR` before parsing cards
- **Row classification**: cell-majority numeric test (NOT character-level `isdigit()`)
- **Rate limit**: 2s between requests (configurable via `settings.py`)
- **Implement phases in order** — each phase verified before next begins

## Verification Commands

```bash
# Phase 0: Session bootstrap
python -c "from tfais.scraper.session_manager import SessionManager; sm = SessionManager(); d = sm.bootstrap(); print(d[:3])"

# Phase 2: Parser smoke test
python -c "from tfais.parser.card_parser import CardParser; cp = CardParser(); print('OK')"

# Phase 5: API server
uvicorn tfais.api.main:app --reload
# Then visit http://127.0.0.1:8000/docs

# Phase 6: Dashboard
streamlit run dashboard/app.py
```
