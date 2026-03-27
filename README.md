# 🌾 TFAIS — Tamil Nadu Fertilizer Availability Intelligence System

An end-to-end data pipeline and analytics dashboard that transforms Tamil Nadu's static government fertilizer portal into a real-time, queryable, and analytics-driven platform.

---

## Problem

The Tamil Nadu government fertilizer portal publishes district-wise dealer stock data, but it is:

- Locked behind a POST-based web form (no API, no CSV export)
- Rendered as card-based HTML with Tamil-language dynamic columns
- Not tracked historically — yesterday's data is gone today

This makes it impossible for policymakers and agricultural officers to monitor shortages, analyze distribution inefficiencies, or build farmer-facing tools.

---

## Solution

TFAIS automates daily scraping, normalizes the data into PostgreSQL, and exposes it via a REST API and Streamlit dashboard.

```
Government Portal (POST form)
        │
        ▼
  SessionManager          ← Phase 0: establishes cookies, extracts district list
        │
        ▼
  FertilizerScraper       ← Phase 1: iterates all district → block pairs
        │
        ▼
  CardParser              ← Phase 2: extracts dealer cards with error isolation
        │
        ▼
  PostgreSQL (via ORM)    ← Phase 3: normalized schema with time-series stock
        │
        ▼
  Orchestrator            ← Phase 4: ties pipeline together with checkpointing
        │
    ┌───┴───┐
    ▼       ▼
 FastAPI  Streamlit       ← Phase 5 & 6: API + dashboard
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running locally or remote)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
```

### 4. Create database schema

```bash
python main.py --create-tables
```

### 5. Discover district codes

```bash
python main.py --list-districts
```

District codes are 4-digit numbers (e.g. `3321` = Thanjavur). Always run this first to see real codes.

### 6. Run a test scrape (1 district)

```bash
python main.py --district 3321
```

### 7. Full scrape (all 38 districts, ~19 min at 2s rate limit)

```bash
python main.py
```

### 8. Start the API

```bash
uvicorn tfais.api.main:app --reload
# API docs: http://127.0.0.1:8000/docs
```

### 9. Start the dashboard

```bash
streamlit run dashboard/app.py
```

---

## Project Structure

```
dashboard/
├── main.py                         # CLI entry point
├── requirements.txt
├── .env.example                    # Config template
├── CLAUDE.md                       # Claude Code context file
│
├── tfais/
│   ├── config/
│   │   └── settings.py             # All config (URLs, DB, timeouts)
│   │
│   ├── scraper/
│   │   ├── session_manager.py      # Phase 0: HTTP session + district/block fetch
│   │   └── scraper.py              # Phase 1: POST-based scraper
│   │
│   ├── parser/
│   │   └── card_parser.py          # Phase 2: HTML card → DealerRecord
│   │
│   ├── database/
│   │   ├── models.py               # SQLAlchemy ORM (7 tables)
│   │   ├── connection.py           # Engine + session factory
│   │   └── operations.py           # Upsert helpers + checkpoint logic
│   │
│   ├── pipeline/
│   │   └── orchestrator.py         # Phase 4: end-to-end pipeline
│   │
│   └── api/
│       └── main.py                 # Phase 5: FastAPI REST endpoints
│
├── dashboard/
│   └── app.py                      # Phase 6: Streamlit dashboard
│
├── tests/
└── logs/
```

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `districts` | Tamil Nadu district reference |
| `blocks` | Blocks/circles per district |
| `dealers` | Fertilizer dealer profiles |
| `fertilizers` | Fertilizer master reference (Tamil names) |
| `fertilizer_stock` | Time-series stock snapshots (fact table) |
| `scrape_metadata` | Per-run stats (started, completed, errors) |
| `scrape_checkpoints` | Block-level resume state |

Dedup key for dealers: `UNIQUE(dealer_code, block_id)` — not license number, which is not visible on result cards.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/districts` | All districts |
| GET | `/blocks?district_code=1` | Blocks for a district |
| GET | `/fertilizer-stock` | Stock records (filterable by district, block, date) |
| GET | `/dealer-details?dealer_code=999210` | Dealer profile + stock history |
| GET | `/summary` | District-level aggregate totals |
| GET | `/health` | Health check |

Full interactive docs: `http://127.0.0.1:8000/docs`

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| District Overview | Summary table + bar chart of total stock per district |
| Stock Trends | Time-series line chart by fertilizer type |
| Fertilizer Comparison | Bar chart of fertilizer availability across dealers |
| Dealer Search | Look up a dealer by code, view contact + stock history |
| Alerts | Low-stock warnings (configurable threshold) |

---

## Design Decisions

### Why POST-based scraping?

The site uses jQuery + AngularJS. District selection fires an AJAX POST to populate the block dropdown. Results are returned via `POST /Fertilizer/result/tm`. There is no URL-based hierarchy to crawl. `requests.Session()` is used throughout to maintain cookies.

### Why card-based parsing?

Results are rendered as Bootstrap card divs — one per dealer — each with an embedded mini-table. Column headers are in Tamil and vary per dealer. The parser uses a multi-strategy selector chain with structural fallback.

### Why per-item error isolation?

With ~570 (district, block) pairs, a single network failure or malformed page must not stop the entire run. Every district and block failure is logged and skipped; the run continues.

### Why a `fertilizers` master table?

Tamil fertilizer names scraped from the site are stored as-is. The master table provides a stable code field for cross-run consistency and a place to add English translations manually over time.

---

## Key Challenges

1. **POST-driven navigation** — no URL crawling possible; requires stateful session
2. **Dynamic Tamil headers** — fertilizer columns differ per dealer and are in Tamil script
3. **Card-based HTML** — each dealer is an individual card, not a flat table row
4. **No historical data** — the portal shows only current stock; time-series is built by daily scraping
5. **~19 min runtime** — 570 requests at 2s each; async option available via `aiohttp`

---

## Configuration

All settings in `tfais/config/settings.py`, overridable via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `tfais` | Database name |
| `DB_USER` | `postgres` | DB user |
| `DB_PASSWORD` | — | DB password |
| `RATE_LIMIT_SECONDS` | `2.0` | Delay between HTTP requests |
| `REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds |
| `LOG_LEVEL` | `INFO` | Logging level |
| `TFAIS_API_URL` | `http://127.0.0.1:8000` | API URL for dashboard |

---

## How to Use

### Scraper

**Step 1 — See all available district codes**

```bash
python main.py --list-districts
```

Output:
```
Available districts (38 total):

  3317  அரியலூர்
  3338  செங்கல்பட்டு
  3302  சென்னை
  3321  தஞ்சாவூர்
  ...

Usage: python main.py --district 3317 3338 3302
```

**Step 2 — Scrape one or more districts**

```bash
# Single district (Thanjavur)
python main.py --district 3321

# Multiple districts
python main.py --district 3321 3317 3302

# All 38 districts (~19 min)
python main.py
```

Each run is tracked in the `scrape_metadata` table with a unique `run_id`. Completed blocks are checkpointed — if the run is interrupted, re-running the same command resumes from where it left off.

**Step 3 — Check what was scraped**

Logs are written to `logs/tfais.log`. The final summary line shows:

```
=== Run Summary ===
  status: completed
  run_id: 4
  districts: 1
  blocks: 8
  dealers_scraped: 318
  errors: 0
```

---

### API

Start the server:

```bash
uvicorn tfais.api.main:app --reload
```

Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`

**Common queries:**

```bash
# List all districts
curl http://127.0.0.1:8000/districts

# Blocks in Thanjavur
curl "http://127.0.0.1:8000/blocks?district_code=3321"

# Fertilizer stock for Thanjavur today
curl "http://127.0.0.1:8000/fertilizer-stock?district_code=3321&scrape_date=2026-03-27"

# District-level totals
curl "http://127.0.0.1:8000/summary?scrape_date=2026-03-27"

# Dealer profile + stock history
curl "http://127.0.0.1:8000/dealer-details?dealer_code=162596"
```

---

### Dashboard

Start the dashboard (API must be running first):

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`

| Page | What it shows | How to use |
|------|--------------|------------|
| **District Overview** | Total stock and dealer count per district | Select a date in the sidebar to view historical data |
| **Stock Trends** | Line chart of fertilizer stock over time | Select a district from the sidebar to filter |
| **Fertilizer Comparison** | Bar chart of which fertilizers are most stocked | Use district filter for a regional view |
| **Dealer Search** | Dealer contact info and stock history | Enter a dealer code (e.g. `162596`) and click Search |
| **Alerts** | Dealers below a stock threshold | Adjust the threshold slider in the sidebar |

**Sidebar controls:**

- **Scrape date** — filter all views to a specific date's data
- **District** — scope views to one district (`All` shows everything)
- **Low-stock threshold (kg)** — controls what counts as a low-stock alert

---

### Diagnostics

If something isn't working, run the site inspection script to dump the live HTML structure:

```bash
python inspect_site.py
# Saves full HTML to logs/site_snapshot.html
# Prints all <select> elements, forms, hidden inputs, and AngularJS attributes
```

Failed card snapshots are saved automatically to `logs/failed_cards/` for offline debugging.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `python main.py` | Full scrape — all 38 districts |
| `python main.py --district 3321 3317` | Scrape specific districts by code |
| `python main.py --list-districts` | Print all district codes and Tamil names |
| `python main.py --create-tables` | Create DB schema and exit (no scrape) |
| `python inspect_site.py` | Dump live site HTML structure for debugging |
| `uvicorn tfais.api.main:app --reload` | Start REST API server |
| `streamlit run dashboard/app.py` | Start Streamlit dashboard |

---

## One-line Pitch

> *Built an end-to-end intelligent system that transforms Tamil Nadu's static fertilizer availability website into a real-time, queryable, and analytics-driven platform for agricultural decision-making.*
