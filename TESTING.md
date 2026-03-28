# TFAIS Testing Guide

## Quick Verification

### 1. Schema & Database
```bash
# Create fresh schema
python main.py --create-tables

# Check table structure
python -c "
from tfais.database.connection import get_engine
from sqlalchemy import inspect
inspector = inspect(get_engine())
for table in inspector.get_table_names():
    print(f'{table}: {[c[\"name\"] for c in inspector.get_columns(table)]}')"
```

### 2. Scraper
```bash
# List available districts
python main.py --list-districts

# Scrape one district
python main.py --district 3321

# Scrape multiple districts
python main.py --district 3321 3339 3301

# Full scrape (all 38 districts)
python main.py
```

### 3. API
```bash
# Start API server
uvicorn tfais.api.main:app --reload

# Test endpoints (in another terminal)
curl http://127.0.0.1:8000/districts
curl http://127.0.0.1:8000/summary
curl "http://127.0.0.1:8000/fertilizer-stock?limit=5"
curl "http://127.0.0.1:8000/dealer-details?dealer_code=364468"

# Interactive docs
Open: http://127.0.0.1:8000/docs
```

### 4. Dashboard
```bash
# Start dashboard
streamlit run dashboard/app.py

# Open in browser
http://localhost:8501

# Test pages
- 📍 Overview: KPI cards + bar chart
- 📊 Supply Matrix: Heatmap + zero-stock
- 📉 Trends: Multi-line with controls
- 🧪 Deep-Dive: Grouped bars + donut
- 🔍 Dealer Intel: Search + history
- ⚠️ Alerts: Severity + treemap
- 🧠 Intelligence: 3 tabs of analysis
```

## Data Schema

### FertilizerStock Table (Critical)
```sql
SELECT
    fs.id,
    fs.dealer_id,
    fs.fertilizer_name,  -- NEW: Direct storage (was fertilizer_id FK)
    fs.quantity,         -- In KG
    fs.unit,            -- NEW: 'KG' default
    fs.scrape_date,     -- NEW: Logical date (was scraped_at)
    fs.created_at,      -- NEW: Metadata timestamp
    fs.scrape_run_id
FROM fertilizer_stock fs
WHERE fs.scrape_date = CURRENT_DATE
LIMIT 10;
```

### Key Differences from Previous Schema

| Aspect | Before | After | Why |
|--------|--------|-------|-----|
| Fertilizer Storage | FK to fertilizers table | Direct VARCHAR(100) | Eliminates JOIN overhead |
| Deduplication | UNIQUE(dealer_code, block_id) | Partial unique WHERE code != '' | Handles empty codes |
| Date Tracking | scraped_at TIMESTAMP | scrape_date DATE + created_at TIMESTAMP | Separate concerns |
| Unit Info | Not stored | unit VARCHAR(10) | Prepare for non-KG quantities |
| Indexes | Separate idx_stock_date, idx_stock_dealer | Composite idx_stock_date_dealer | Query planner optimization |

## Test Scenarios

### Scenario 1: Fresh Setup
```bash
python main.py --create-tables
python main.py --district 3321
# Expected: 1 district, ~8 blocks, ~100+ dealers scraped
curl http://127.0.0.1:8000/summary
# Expected: district_code=3321, total_dealers > 50, total_stock_kg > 0
```

### Scenario 2: Multi-Date Comparison
```bash
# Scrape on Day 1
python main.py --district 3321

# Wait or modify some data
# Scrape again
python main.py --district 3321

# View trends
# Open dashboard → 📉 Trends page
# See day-over-day % change
```

### Scenario 3: Low-Stock Alerts
```bash
# In dashboard, set threshold to 5000 kg
# Go to ⚠️ Alerts page
# Expected: See critical/warning/caution tiers
# Expected: Treemap shows severity hierarchy
```

### Scenario 4: Intelligence Analysis
```bash
# Need multi-day data (≥2 scrapes)
# Go to 🧠 Intelligence page

# Tab 1: Stock Concentration
# Select a fertilizer (e.g., 'டி ஏ பி')
# Hover pie charts showing top-5 dealer share
# Expected: Red (>80%), Yellow (60-80%), Green (<60%)

# Tab 2: Coverage Gaps
# See blocks without stock of specific fertilizers
# Expected: Expandable list of gaps

# Tab 3: Volatility
# See dealers with unstable stock day-to-day
# Expected: Coefficient of variation bar chart (requires ≥3 data points)
```

## Common Issues & Fixes

### Issue: "No data available"
**Cause**: Haven't run scraper yet
**Fix**:
```bash
python main.py --create-tables
python main.py --district 3321  # Or your test district
```

### Issue: "Could not reach API"
**Cause**: API not running on port 8000
**Fix**:
```bash
uvicorn tfais.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Issue: Dashboard shows empty tables
**Cause**: Date picker is filtering to future date
**Fix**:
- Don't select a date (leave blank for all dates)
- Or select a date when you ran the scraper

### Issue: Volatility tab shows "Insufficient data"
**Cause**: Need ≥3 scrape dates for volatility calculation
**Fix**: Run scraper on multiple different days
```bash
python main.py --district 3321  # Day 1
# (wait/come back next day)
python main.py --district 3321  # Day 2
python main.py --district 3321  # Day 3
```

## Performance Notes

### Query Performance
- Dashboard filters by `scrape_date, dealer_id` → Uses composite index
- Expected response time: <500ms for 1000 rows
- Cached with 5-minute TTL to reduce API load

### Data Size
- 38 districts × ~10 blocks × ~10 dealers × ~8 fertilizers = ~30k rows per day
- One month of daily scrapes = ~900k rows
- Indexes ensure queries stay sub-second even at scale

## Database Validation

```bash
# Check all constraints
python -c "
from tfais.database.connection import get_engine
from sqlalchemy import inspect

inspector = inspect(get_engine())

# Check primary keys
for table in ['districts', 'blocks', 'dealers']:
    pk = inspector.get_pk_constraint(table)
    print(f'{table}: PK={pk[\"constrained_columns\"]}')

# Check indexes
for table in ['fertilizer_stock', 'scrape_checkpoints']:
    indexes = inspector.get_indexes(table)
    for idx in indexes:
        print(f'{table}: {idx[\"name\"]} on {idx[\"column_names\"]}')"
```

## Cleanup (Reset Everything)

```bash
# WARNING: Destructive - removes all data
python -c "
from tfais.database.connection import drop_all_tables, create_all_tables
drop_all_tables()
create_all_tables()
print('Database reset.')"

# Then scrape fresh data
python main.py --district 3321
```

---

**Last Updated**: 2026-03-28
**Schema Version**: 6 tables (post-critique fixes)
