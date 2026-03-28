# TFAIS Improvements Summary (2026-03-28)

## Overview

This session completed two major improvements to the TFAIS system:
1. **Database Schema Hardening** — Addressed critical production issues identified in senior backend review
2. **Dashboard Redesign** — Upgraded from 5 basic pages to 7 advanced analytics pages with Plotly visualizations

---

## Part 1: Database Schema Fixes

### Problem Statement
The initial schema was over-engineered for MVP and had design issues that would cause problems at scale:
- Unnecessary `fertilizers` master table adding query overhead
- Deduplication bugs when dealer codes were empty
- Conflated logical dates with insertion timestamps
- Suboptimal indexes for the dashboard's primary query pattern

### Changes Made

#### 1. Dropped `fertilizers` Master Table
**Before**: 7 tables with `fertilizers → fertilizer_stock` FK relationships
```sql
SELECT fs.quantity FROM fertilizer_stock fs
JOIN fertilizers f ON fs.fertilizer_id = f.id WHERE f.code = 'DAP'
```

**After**: 6 tables with `fertilizer_name` stored directly as VARCHAR(100)
```sql
SELECT quantity FROM fertilizer_stock WHERE fertilizer_name = 'DAP'
```

**Benefits**:
- Eliminates join overhead (1 fewer table for every stock query)
- Removes dependency on maintaining a fertilizer master list
- Storage: ~8-15 fertilizer names per day → no duplication in fact table
- Simpler data pipeline (no `upsert_fertilizer()` call)

#### 2. Fixed Deduplication (Partial Unique Index)
**Before**: `UNIQUE(dealer_code, block_id)` violates when `dealer_code = ''`
```sql
-- This fails when second dealer in block has empty code:
INSERT INTO dealers (dealer_code='', block_id=5, name_ta='...')
INSERT INTO dealers (dealer_code='', block_id=5, name_ta='...') -- VIOLATION
```

**After**: Partial unique index that skips empty codes
```sql
CREATE UNIQUE INDEX idx_dealer_dedup
ON dealers(dealer_code, block_id) WHERE dealer_code != '';

-- Both inserts succeed:
INSERT INTO dealers (dealer_code='', block_id=5, name_ta='Store A') -- OK
INSERT INTO dealers (dealer_code='', block_id=5, name_ta='Store B') -- OK
INSERT INTO dealers (dealer_code='12345', block_id=5, ...) -- Enforced unique
```

**Benefits**:
- Handles dealer cards with missing/unextractable codes
- Still prevents duplicate dealers with the same code

#### 3. Split `scraped_at` → `scrape_date` + `created_at`
**Before**: Single `scraped_at` TIMESTAMP conflated logical date with insertion time
```sql
scraped_at TIMESTAMP  -- Ambiguous: is this "data is for 2026-03-28" or "inserted at 15:42:30"?
```

**After**: Separate columns with clear semantics
```sql
scrape_date  DATE       -- Logical: "This data represents this date"
created_at   TIMESTAMP  -- Metadata: "When was this row inserted?"
```

**Benefits**:
- UNIQUE constraint is now on `(dealer_id, fertilizer_name, scrape_date)` — one reading per dealer per fertilizer per day
- Insertion time is metadata (for audit trails, not business logic)
- Dashboard queries filter on logical date: `WHERE scrape_date = '2026-03-28'`

#### 4. Added `unit` Column
```sql
unit VARCHAR(10) DEFAULT 'KG'  -- 'KG', 'BAGS', 'TONNES', etc.
```

**Benefits**:
- Prepares for future non-KG quantities (some fertilizers might be in 50kg bags)
- Prevents silent data corruption if quantity semantics change
- Query transparency: `SELECT quantity, unit FROM fertilizer_stock`

#### 5. Optimized Indexes
**Before**: Separate indexes
```sql
CREATE INDEX idx_stock_date ON fertilizer_stock(scrape_date)
CREATE INDEX idx_stock_dealer ON fertilizer_stock(dealer_id)
```

**After**: Composite index matching dashboard's primary query pattern
```sql
CREATE INDEX idx_stock_date_dealer ON fertilizer_stock(scrape_date, dealer_id)
```

**Benefits**:
- Database query planner can use a single index for: `WHERE scrape_date = ? AND dealer_id IN (...)`
- Significant speedup for dashboard's "show me stock for district X on date Y" query
- No table scan needed

#### 6. Added Operational Columns
```sql
-- scrape_runs table
trigger_type VARCHAR(20) DEFAULT 'manual'  -- manual/scheduled/resume

-- dealers table
updated_at TIMESTAMP DEFAULT NOW()  -- Track when contact/address last changed
```

**Benefits**:
- Track how scrape runs were initiated (helps debugging overlaps)
- Know if dealer contact info is fresh or stale

### Files Modified
- **tfais/database/models.py**: Removed `Fertilizer` ORM, updated `FertilizerStock`
- **tfais/database/operations.py**: Removed `upsert_fertilizer()`, simplified `persist_dealer_record()`
- **tfais/api/main.py**: Updated response models to use `quantity` field
- **dashboard/app.py**: Updated field references (`quantity_kg` → `quantity`, `scraped_at` → `scrape_date`)

### Verification
✓ Schema created successfully: `python main.py --create-tables`
✓ Test scrape completed: 106 dealers from district 3339 persisted
✓ API endpoints responding: `/summary`, `/fertilizer-stock`, `/districts`
✓ All 6 tables with correct columns and indexes

---

## Part 2: Dashboard Redesign

### Problem Statement
Original dashboard had 5 pages with basic `st.bar_chart` and `st.line_chart` visualizations:
- No interactivity (hover data, drill-down)
- Limited analytical depth
- No decision-support features

### Solution: 7-Page Plotly Dashboard

#### Page 1: 📍 Overview (Redesigned)
**Components**:
- **KPI Cards with Deltas**: Districts, Total Dealers, Total Stock (T), Low-Stock Count
  - Shows day-over-day change from previous scrape
  - Auto-calculates comparison date
- **Color-Coded Bar Chart**: Stock by district
  - Red (🔴) → Yellow (🟡) → Green (🟢) scale
  - Hover shows exact quantities
  - Sorted by stock amount
- **Summary Table**: District details (dealers count, stock, last scraped)

**Data Source**: `/summary` endpoint

#### Page 2: 📊 Supply Matrix (NEW)
**Purpose**: Instant visual identification of supply gaps

**Components**:
- **Heatmap**: District rows × Fertilizer columns
  - Green = high stock, Red = zero stock
  - Hover shows exact quantities
  - Auto-scales based on data dimensions
- **Zero-Stock Warnings**: Table listing all (district, fertilizer) pairs with ZERO stock
  - Helps identify supply deserts

**Use Case**: "Which fertilizers are missing in which districts?"

#### Page 3: 📉 Trends (Enhanced)
**Components**:
- **Granularity Selector**: Daily / Weekly / Monthly aggregation
- **Drill-Down Selector**: State Total / By District
- **Multi-Line Chart**: Fertilizer lines with markers and hover data
  - Unified hover mode shows all series values
  - Color-coded by fertilizer type
- **Day-over-Day % Change Table** (daily only):
  - Shows %change from previous day
  - Conditional formatting (red/yellow/green)

**Use Case**: "How are stock levels trending? Is DAP recovering?"

#### Page 4: 🧪 Deep-Dive (Enhanced)
**Components**:
- **Grouped Bar Chart** (left): Fertilizer × District
  - Groups fertilizers, colors by district
  - Shows inter-district comparison per fertilizer
- **Donut Chart** (right): Stock share by fertilizer
  - Percentage of total + label inside
  - Color-coded
- **Top 20 Dealers Table**: Cumulative stock across all fertilizers

**Use Case**: "Which fertilizer type has most stock? Which dealers dominate?"

#### Page 5: 🔍 Dealer Intel (Enhanced)
**Components**:
- **Dealer Search**: Code-based lookup
- **Contact Card**: Block, District, Address, Phone
- **Stock History Line Chart** (new): Multi-fertilizer time-series
  - Shows how this dealer's inventory changed over time
  - Color by fertilizer
- **Browse by Block**: Table of all dealers in selected district
  - Filterable, sortable

**Use Case**: "What's this dealer's contact? Have they been restocking DAP?"

#### Page 6: ⚠️ Alerts (Redesigned)
**Components**:
- **Severity Tiers** (3 metric cards):
  - 🔴 Critical (<100kg): Immediate action needed
  - 🟡 Warning (<300kg): Monitor closely
  - 🟠 Caution (<threshold): Stock up soon
- **Treemap**: Alert distribution by severity → district → dealer
  - Area = stock quantity
  - Color = severity
  - Click → drill down
- **Alert Details Table**: Sortable/filterable
  - District, Block, Dealer, Fertilizer, Stock, Severity

**Use Case**: "What are the worst low-stock situations? How many dealers are critical?"

#### Page 7: 🧠 Intelligence (NEW)
**Three tabs for strategic supply chain insights**:

**Tab 1: Stock Concentration**
- **Question**: "Which dealers hold 80%+ of the supply? (monopoly risk)"
- **Visualization**: Pie charts per (district, fertilizer)
  - Color-coded risk: 🔴 >80%, 🟡 >60%, 🟢 <60%
- **Use Case**: "If one dealer stops supplying, how bad is the shortage?"

**Tab 2: Coverage Gaps**
- **Question**: "Which blocks have ZERO stock of which fertilizers?"
- **Visualization**: Expanders per fertilizer type
  - Lists all blocks without that fertilizer
  - Shows district, block
- **Use Case**: "Where are supply deserts? Which areas need emergency allocation?"

**Tab 3: Stock Volatility**
- **Question**: "Which dealers' inventory swings wildly day-to-day?"
- **Metric**: Coefficient of Variation (σ/μ × 100)
- **Visualization**: Bar chart, top 20 most volatile dealers
  - Hover shows mean, std, count
  - Red (🔴) = high volatility (supply chain risk)
- **Prerequisite**: Multi-day data (≥3 scrapes)
- **Use Case**: "Which dealers are unreliable suppliers? Who should we diversify away from?"

### Sidebar Controls (All Pages)
- **Date Picker**: Filter all visualizations to specific scrape date
- **District Selector**: "All" or specific district
- **Low-Stock Threshold**: Slider (0-5000kg) for Alerts & Intelligence pages

### Technical Implementation

#### Imports
```python
import plotly.express as px        # Declarative charts
import plotly.graph_objects as go  # Advanced customization
import streamlit as st              # Dashboard framework
```

#### Caching
```python
@st.cache_data(ttl=300)  # 5-minute cache for API calls
def fetch_stock(...) -> pd.DataFrame
```

#### Key Patterns
- **Data fetching**: All API calls cached with TTL
- **Lazy loading**: Fetch data only for selected page
- **Color schemes**: Consistent red/yellow/green for stock levels
- **Hover data**: All charts show exact values on hover
- **Responsive layout**: st.columns for side-by-side visualizations

### Files Modified
- **dashboard/app.py**: Complete rewrite (68 lines → 600+ lines)
  - Added Plotly imports
  - Restructured into 7 page sections
  - Implemented all new pages and tabs
  - Added concentration, gap, and volatility calculations

### Verification
✓ Dashboard syntax check: Valid Python AST
✓ Imports check: All modules load successfully
✓ Manual test: Dashboard starts without errors
✓ Page navigation: All 7 pages accessible via sidebar radio

---

## Benefits Summary

### Database Schema Benefits
1. **Performance**: Fewer joins, optimized indexes → faster dashboard queries
2. **Data Quality**: Partial unique index prevents duplication bugs
3. **Flexibility**: Separate scrape_date/created_at enables audit trails
4. **Scalability**: Direct fertilizer_name storage scales better than master table
5. **Maintainability**: Simpler ORM, fewer operations functions

### Dashboard Benefits
1. **Interactivity**: Hover data, drill-down, color-coding
2. **Decision Support**: Intelligence page provides strategic insights
3. **Speed**: Plotly renders client-side, no server overhead
4. **Flexibility**: Sidebar controls (date, district, threshold) apply across all pages
5. **Comprehensiveness**: 7 pages cover operational, tactical, and strategic needs
6. **User Experience**: Consistent color scheme, intuitive navigation, clear titles

---

## Testing & Validation

### Schema Tests
```
[PASS] All 6 tables exist: districts, blocks, dealers, fertilizer_stock, scrape_runs, scrape_checkpoints
[PASS] FertilizerStock has all required columns: id, dealer_id, fertilizer_name, quantity, unit, scrape_date, created_at
[PASS] All ORM models import successfully
[PASS] All database operations import successfully
```

### API Tests
```
[PASS] GET /districts → 200 OK
[PASS] GET /summary → 200 OK
[PASS] GET /fertilizer-stock?limit=1 → 200 OK
```

### Dashboard Tests
```
[PASS] dashboard/app.py syntax is valid
[PASS] All Plotly imports available
[PASS] Dashboard starts without runtime errors
[PASS] All 7 pages load correctly
```

### End-to-End Integration Test
```
[PASS] python main.py --create-tables → Creates fresh schema
[PASS] python main.py --district 3339 → Scrapes 106 dealers
[PASS] All data persists correctly with new schema
[PASS] API returns correct field names (quantity, scrape_date, unit)
[PASS] Dashboard displays data without errors
```

---

## Deployment Checklist

- [x] Database schema updated and verified
- [x] All field references updated in API and dashboard
- [x] Test scrape completed successfully
- [x] All pages tested and working
- [x] Code committed to git

### Ready to Deploy
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies (if needed)
pip install -r requirements.txt

# 3. Create fresh database (or migrate existing)
python main.py --create-tables

# 4. Optional: Run a test scrape
python main.py --district 3301  # Your preferred test district

# 5. Start API
uvicorn tfais.api.main:app --reload

# 6. Start dashboard (in separate terminal)
streamlit run dashboard/app.py
```

---

## Future Enhancements (Not in Scope)

- Real-time WebSocket updates instead of polling
- Map visualization of districts
- Predictive analytics (demand forecasting)
- Multi-user authentication & RBAC
- Alerts/notifications system
- Export to Excel/PDF reports
- Historical comparison (year-over-year)
- Fertilizer name translation (Tamil ↔ English)

---

**Session Date**: 2026-03-28
**Commits**:
- `74a2201` - Fix database schema per senior backend critique
- `da3860c` - Redesign Streamlit dashboard: 5 → 7 pages with Plotly
