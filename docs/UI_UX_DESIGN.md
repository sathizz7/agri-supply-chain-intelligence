# TFAIS Frontend UI/UX Design System

## Overview

A professional, government-grade agriculture intelligence dashboard designed in Stitch for monitoring fertilizer stock across Tamil Nadu's 38 districts. The design targets agriculture officers and policymakers with decision-making UX prioritized over decoration.

**Stitch Project:** `TFAIS — Tamil Nadu Fertilizer Intelligence Dashboard`
**Project ID:** `12620894926771058047`
**Design System Asset ID:** `2904128892002282564`

---

## Design System Specifications

### Color Palette

| Color | Hex | Usage | Semantics |
|-------|-----|-------|-----------|
| Primary Green | `#1B7A3D` | Navigation, primary buttons, healthy stock | Authority, growth, agriculture |
| Amber/Warning | `#F39C12` | Warning-level alerts (100-300kg), secondary highlights | Caution, action needed |
| Red/Critical | `#E74C3C` | Critical alerts (<100kg), urgent status | Danger, requires immediate action |
| Yellow/Caution | `#F1C40F` | Caution-level alerts (300-500kg) | Attention, monitor closely |
| Green/Adequate | `#27AE60` | Healthy stock levels | All clear, no action needed |
| Neutral Background | `#F8F9FA` | Page backgrounds, subtle contrast | Clean, professional |
| White | `#FFFFFF` | Cards, panels, content areas | Trust, clarity |

**Severity Color Scale (for choropleths, heatmaps, stock indicators):**
```
Red (#E74C3C) → Amber (#F39C12) → Yellow (#F1C40F) → Green (#27AE60)
Critical      Warning          Caution           Adequate
```

### Typography

| Element | Font | Usage | Weight |
|---------|------|-------|--------|
| Page Titles | Inter Bold | "District-wise Availability", route headers | 700 |
| KPI Numbers | Inter Bold | Large metric values ("38", "85.3 T") | 700 |
| Body Text | Inter Regular | Table data, descriptions, form labels | 400 |
| Chart Labels | Space Grotesk | Axis labels, legend entries, badges | 500 |
| Badges/Tags | Space Grotesk | "Critical", "Warning", "Adequate" | 600 |

### Spacing & Roundness

- **Border Radius:** 8px (ROUND_EIGHT) — consistent across cards, buttons, badges
- **Card Shadows:** Subtle elevation (1-2px shadow)
- **Padding:** 16-24px inside cards
- **Gap between sections:** 24px

---

## Layout Architecture

### Global Structure

```
┌─────────────────────────────────────────┐
│  Top Bar (90px)                         │
│  [Logo] [Date] [District] [Threshold]   │
├──────────┬──────────────────────────────┤
│ Sidebar  │ Main Content Area            │
│ (240px)  │ (Scrollable)                 │
│ (Dark    │                              │
│  Green)  │ Page: Route-specific content │
│          │                              │
│ 8 Routes │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

### Responsive Behavior

- **Desktop (>1024px):** Full sidebar + top bar + content
- **Tablet (768-1024px):** Sidebar collapsible to icons only
- **Mobile (<768px):** Sidebar collapses to hamburger menu, full-width content

---

## 9 Screen Designs

### 1. **Overview Dashboard** (`/overview`)

**Purpose:** State-wide snapshot and entry point for all users.

**Key Sections:**
- **KPI Row:** 4 metric cards (Districts, Active Dealers, Total Stock in T, Low-Stock Alerts)
  - Large numbers with delta indicators (green ↑ for increase, red ↓ for decrease)
  - Cards have subtle shadows and rounded corners

- **Mini Choropleth Map (60% width)**
  - Tamil Nadu district boundaries
  - Fill color by stock level (severity scale)
  - Color legend (bottom-right)
  - Link: "Explore Full Map →"

- **District Ranking Bar Chart (40% width)**
  - Top 10 districts by stock
  - Horizontal bars, color-coded by severity
  - Sorted descending
  - Rounded bar ends

- **Summary Table (full width, below charts)**
  - Columns: District | Dealers | Total Stock (kg) | Last Scraped
  - Sortable headers with arrows
  - Zebra striping (alternate row colors)
  - Search/filter input above

**User Flow:** Morning briefing — scan KPIs → check top districts → investigate details

---

### 2. **Map Explorer** (`/map`)

**Purpose:** Interactive GIS exploration with drill-down capability.

**Key Sections:**
- **Full-screen OpenLayers Map**
  - All 38 districts as polygons
  - Fill color by stock level (severity scale)
  - One district highlighted with thicker border and glow
  - OSM basemap (subtle gray)
  - Zoom controls (top-left)
  - Layer toggle button

- **Hover Tooltip**
  - District name (Tamil)
  - Total Stock
  - Dealer count
  - Status badge (color-coded)

- **Right Info Panel (350px wide, slide-in)**
  - District name with close (X) button
  - 3 summary metric cards: Dealers, Stock (kg), Blocks
  - **Blocks List** — clickable rows with dealer count and stock indicator dots
  - **Quick Stock Table** — Fertilizer | Stock | Status (small, 5 rows)
  - Footer button: "View Full Details →"

**User Flow:** Spatial discovery — click district → explore blocks → drill into dealer

---

### 3. **Alerts** (`/alerts`)

**Purpose:** Emergency response and low-stock monitoring.

**Key Sections:**
- **Page Title:** "Low-Stock Alerts" with threshold subtitle

- **3 Severity Cards (equal width)**
  - Critical (<100kg): Red card, large count, red background tint
  - Warning (<300kg): Amber card, large count, amber background tint
  - Caution (<500kg): Yellow card, large count, yellow background tint
  - Left colored border on each card for visual weight

- **Treemap (full width, ~400px)**
  - Hierarchy: Severity → District → Dealer
  - Rectangles sized by stock quantity
  - Fill color by quantity (severity scale)
  - Labels inside larger rectangles
  - Title: "Alert Distribution by District & Dealer"

- **Alert Details Table (full width, sortable)**
  - Columns: Severity | District | Block | Dealer | Fertilizer | Stock (kg)
  - Severity shown as colored badge pill
  - Rows sorted by quantity ascending (worst first)
  - Dealer names are clickable links
  - Export CSV button (top-right)
  - Pagination at bottom

**User Flow:** Crisis response — identify severity → locate geographically → contact dealers

---

### 4. **Dealer Detail** (`/dealers/:dealerCode`)

**Purpose:** Individual dealer profile and stock history.

**Key Sections:**
- **Dealer Profile Card (full width, white, shadow)**
  - Left: Large name (Tamil) + dealer code badge
  - Below: Block, District, Contact (with phone icon and "Call" button)
  - Address line below
  - Right: "View on Map" and "Export History" action buttons

- **4 Stock Overview Cards (equal width)**
  - One per fertilizer type: Urea, DAP, NPK, MOP
  - Large quantity in kg
  - Color-coded by severity (green/amber/red)
  - Severity badge if not adequate
  - Sparkline trend (7-day)

- **Stock History Line Chart (full width, ~350px)**
  - Title: "Stock History — Last 30 Days"
  - Multi-line chart: 4 lines (one per fertilizer)
  - X-axis: Dates | Y-axis: Quantity (kg)
  - Unified hover tooltip
  - Horizontal red dashed line at 100kg: "Critical threshold"
  - Light grid background

- **Stock History Table (full width, sortable)**
  - Columns: Date | Fertilizer | Quantity (kg) | Unit | Status
  - Status as colored badge (green "Adequate", amber "Warning", red "Critical")
  - Search/filter input above

**User Flow:** Investigate dealer health — review profile → spot trends → take action

---

### 5. **Supply Matrix** (`/supply-matrix`)

**Purpose:** District × Fertilizer coverage analysis and gap identification.

**Key Sections:**
- **Page Title:** "Supply Matrix: District × Fertilizer"

- **Heatmap (full width, ~500px)**
  - Y-axis: Districts (Tamil names, ~15 visible, scrollable)
  - X-axis: Fertilizer types (Urea, DAP, NPK, MOP, SSP, Potash, Zinc Sulphate, Gypsum)
  - Cells colored by quantity (Red-Yellow-Green severity scale)
  - Cell values show quantity in kg
  - Zero-stock cells: Dark red background with white "0"
  - Color legend on right

- **Warning Banner (amber/yellow card)**
  - "⚠ 23 district-fertilizer combinations have ZERO stock"
  - Expandable/collapsible

- **Zero-Stock Table (full width)**
  - Columns: District | Fertilizer | Last Available | Action
  - Action links: "Investigate →"
  - Sortable, searchable
  - ~8 rows

**User Flow:** Supply chain planning — scan heatmap for red → identify gaps → plan redistribution

---

### 6. **Trends** (`/trends`)

**Purpose:** Temporal analysis with multi-granularity support.

**Key Sections:**
- **Page Title:** "Stock Trends Over Time"

- **Control Row (horizontal pill buttons)**
  - Aggregation: Daily (active) | Weekly | Monthly
  - View: State Total (active) | By District

- **Main Line Chart (full width, ~450px)**
  - Title: "State-wide Fertilizer Stock Trend"
  - X-axis: Dates (last 30 days) | Y-axis: Stock (kg)
  - 5 colored lines with markers: Urea, DAP, NPK, MOP, SSP
  - Unified hover tooltip
  - Legend at bottom (colored circles + names)
  - Light gray grid background
  - Slight curve smoothing on lines

- **Auto-Insight Box (light green, rounded)**
  - Natural language insight: "DAP stock declined 18% over the last 7 days. Ariyalur and Dharmapuri account for 65% of the state-wide decline."

- **Day-over-Day Table (full width)**
  - Title: "Daily Change (%)" — Last 7 days
  - Rows: Dates (descending) | Columns: Fertilizer types
  - Values: Percentage change (green text for +, red for -, gray for 0)
  - Bold for ±10% or more
  - Zebra striping

**User Flow:** Trend spotting — check daily changes → identify commodities in decline → investigate regions

---

### 7. **Deep-Dive Analysis** (`/deep-dive`)

**Purpose:** Fertilizer-level commodity analysis and dealer ranking.

**Key Sections:**
- **Page Title:** "Fertilizer-wise Availability"

- **Two-Column Layout:**

  **Left (65%): Grouped Bar Chart**
  - Title: "Fertilizer Stock by District"
  - X-axis: Fertilizers | Y-axis: Stock (kg)
  - Grouped bars by district (5-6 colors)
  - Bar labels on hover
  - District legend with color swatches
  - ~400px height

  **Right (35%): Donut Chart**
  - Title: "Stock Share by Fertilizer"
  - Large donut with center text: "Total: 85.3T"
  - 5 colored segments (Urea largest, then DAP, NPK, MOP, SSP)
  - Percentage labels outside segments
  - Legend below

- **Top Dealers Table (full width, below charts)**
  - Title: "Top 20 Dealers by Total Stock"
  - Columns: # | Dealer Name | Block | District | Total Stock (kg) | Top Fertilizer
  - Rank number in first column
  - Inline data bar visualization for stock column
  - Dealer names are clickable links (green)
  - Show 10 rows with "Show More" button
  - Zebra striping, sortable

**User Flow:** Commodity intelligence — understand product distribution → identify key dealers → monitor concentration

---

### 8. **Dealer Search & Browse** (`/dealers`)

**Purpose:** Fast dealer lookup and directory.

**Key Sections:**
- **Page Title:** "Dealer Contact & Stock Intelligence"

- **Search Card (full width, white, shadow)**
  - Large search input: "Search by dealer code (e.g., 999210)"
  - Green "Search" button
  - Quick filters below: District dropdown, Block dropdown, Status filter (All/Critical/Warning/Adequate)

- **Dealer List (default view)**
  - Title: "All Dealers" with count "(4,218 dealers)"
  - Toggle buttons: Grid view | List view (list is default)

  **List View:**
  - Sortable table: Dealer Code | Dealer Name (Tamil) | Block | District | Stock Status | Actions
  - Stock Status: Colored badge (green/amber/red)
  - Actions: Eye icon (View Details), map pin icon (View on Map)
  - ~10 rows per page
  - Pagination: "Page 1 of 85" with prev/next + input
  - Zebra striping, clickable rows

- **Quick Stats Sidebar (optional, right side, ~250px)**
  - Total Dealers: 4,218
  - Critical: 12 (red dot)
  - Warning: 45 (amber dot)
  - Adequate: 4,161 (green dot)
  - Horizontal stacked bar showing proportions

**User Flow:** Dealer directory — search by code or browse → view details → monitor health

---

### 9. **Intelligence** (`/intelligence`)

**Purpose:** Strategic supply chain analysis (3 tabs).

**Key Sections:**
- **Page Title:** "Supply Intelligence" with subtitle "Data-driven insights for supply chain decision-making"

- **Tab Bar (3 tabs, rounded segment control, green active state)**
  - Tab 1: "Stock Concentration" (active)
  - Tab 2: "Coverage Gaps"
  - Tab 3: "Stock Volatility"

**Tab 1: Stock Concentration**
- Subtitle: "Shows what % of a fertilizer's stock is held by top-5 dealers (monopoly risk)"
- Fertilizer selector dropdown: "Urea" (selected)

- **District Cards (expandable accordion rows, ~4 visible)**
  - Header: Color indicator (red/amber/green circle) + District name (Tamil) + "Top 5 hold XX%" + expand arrow
  - Example expanded row:
    - Indicator: 🔴 Red circle
    - Text: "அரியலூர் (Ariyalur) — Top 5 hold 92%"
    - Content: Pie chart (5 dealer colors) + warning "High concentration risk: 92% held by 5 dealers"
  - Collapsed rows below (amber, then green indicators)

- **Summary Insight Box (bottom, light blue/green background, rounded)**
  - "3 of 38 districts have high concentration risk (>80%). Consider diversifying dealer allocation in Ariyalur, Dharmapuri, and Perambalur."

**User Flow:** Strategic planning — identify concentration risk → monitor dealer diversity → make allocation decisions

---

## Component Patterns

### KPI Card
```
┌─────────────────┐
│  Metric Label   │ (smaller text, gray)
│   38            │ (large number, green or primary)
│   ↑ +124        │ (delta badge, color-coded)
└─────────────────┘
```

### Severity Badge
```
🔴 Critical (<100kg)   [red background, white text, rounded]
🟡 Warning (<300kg)    [amber background, white text, rounded]
🟠 Caution (<500kg)    [yellow background, white text, rounded]
```

### Info Panel (Map)
```
┌─────────────────────┐
│ District Name    [X]│
│─────────────────────│
│ 45 Dealers | 2.1MT  │
│─────────────────────│
│ Blocks:             │
│ ▸ Block A: 20 dealers
│ ▸ Block B: 18 dealers
│─────────────────────│
│ Fertilizer | Stock  │
│─────────────────────│
│ Urea | 1,250 kg    │
│ DAP  | 85 kg (🔴)   │
│─────────────────────│
│ [View Full Details] │
└─────────────────────┘
```

### Data Table
```
┌────────────────────────────────────────────┐
│ District    │ Stock    │ Status   │ Action  │
├────────────────────────────────────────────┤
│ Ariyalur    │ 2,100 kg │ Warning  │ →       │
│ Vellore     │ 5,400 kg │ Adequate │ →       │
│ Tiruppur    │ 1,200 kg │ Critical │ →       │
└────────────────────────────────────────────┘
(Zebra striping, sortable headers, hover highlight)
```

---

## Interaction Patterns

### Click-Through Navigation
- Every district name is a clickable link (green, underlined)
- Every dealer code is a clickable link → `/dealers/:code`
- Every chart element (bar, line, segment) is interactive
- Breadcrumbs available on detail pages

### Filters & State Persistence
- **Top Bar Filters:**
  - Date picker: Applies to all pages (except Trends, which shows multi-day)
  - District selector: Filters all data to selected district
  - Threshold slider: Adjusts low-stock alert cutoff
  - All filter changes persist across route navigation (Zustand store)

### Hover & Tooltips
- **Map:** Hover district polygon → tooltip with summary
- **Charts:** Hover point/bar → unified tooltip showing all related values
- **Tables:** Hover row → subtle highlight (background color change)

### Expandable Sections
- Intelligence Tab 1: District cards are accordion-style (click to expand, pie chart shows)
- Intelligence Tab 2: Fertilizer groups are expandable (list zero-stock pairs)

---

## Accessibility & Responsive Design

### Mobile (< 768px)
- Sidebar collapses to hamburger menu (top-left)
- Full-width content
- Charts and tables stack vertically
- Font sizes adjusted for readability
- Touch targets: minimum 44×44px

### Tablet (768px – 1024px)
- Sidebar collapses to icons only (show tooltip on hover)
- Content area expands
- Two-column layouts may stack

### Desktop (> 1024px)
- Full sidebar with labels
- Multi-column layouts preserved
- Map takes full height on /map route

### Color Contrast
- All text meets WCAG AA standards (4.5:1 ratio for normal text)
- Severity colors chosen for colorblind accessibility (not red/green alone, include position/text)

### Keyboard Navigation
- Tab through controls in logical order
- Enter to activate buttons/links
- Arrow keys for table navigation
- Escape to close modals/panels

---

## Implementation Notes for React Frontend

### Design System Assets

**Colors:** Apply via Tailwind custom colors or CSS variables:
```css
--primary-green: #1B7A3D
--warning-amber: #F39C12
--critical-red: #E74C3C
--caution-yellow: #F1C40F
--success-green: #27AE60
--neutral-bg: #F8F9FA
```

**Typography:**
- Use Inter for headlines and body (Google Fonts)
- Use Space Grotesk for labels/badges (Google Fonts)

**Components to build:**
- `<KPICard>` with metric, label, and optional delta badge
- `<SeverityBadge>` for Critical/Warning/Caution pills
- `<DataTable>` with sortable headers, zebra striping, pagination
- `<DistrictChoropleth>` OpenLayers layer component
- `<InfoPanel>` slide-in panel for map drill-down
- `<TrendChart>` multi-line Plotly chart with unified tooltip
- `<HeatmapChart>` district × fertilizer matrix

### Spacing System
```
4px:   xs (1 unit)
8px:   sm (2 units)
16px:  md (4 units)
24px:  lg (6 units)
32px:  xl (8 units)
```

### Shadow System
- Cards: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1)`
- Elevated UI: `box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1)`
- Modals: `box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15)`

---

## Design System Asset

**Stitch Design System ID:** `assets/2904128892002282564`

Apply this design system to all screens to ensure:
- Consistent color palette
- Inter font family
- 8px border radius
- Light mode color scheme
- Professional government UI appearance

---

## User Personas & Workflows

### Persona 1: District Agriculture Officer (Primary User)
**Morning routine (5 min):**
1. /overview → Check KPIs and deltas
2. /alerts → Any critical (🔴) today?
3. Breadcrumb back to /overview

**Alert response (10 min):**
1. /alerts → Find critical alert
2. Click district in treemap → filter alerts
3. Click dealer link → /dealers/:code
4. Check stock history chart → call dealer

### Persona 2: State-Level Policymaker (Secondary User)
**Weekly strategic review (30 min):**
1. /overview → State-wide KPIs
2. /map → Visualize supply distribution
3. /intelligence → Check concentration risk
4. /trends → Identify declining commodities
5. Export summary to PDF for meeting

### Persona 3: Supply Chain Logistician (Tertiary User)
**Planning (20 min):**
1. /supply-matrix → Find zero-stock gaps
2. /dealers → Search alternate sources
3. /deep-dive → Check dealer capacity
4. Export dealer list to CSV for outreach

---

## Design Principles Applied

1. **Information Hierarchy:** Most important metrics (KPIs) above fold, detailed tables below
2. **Color as Semantic:** Red = danger, Amber = warning, Green = good — consistent everywhere
3. **Click-through Analysis:** Every data point is a potential starting point for investigation
4. **Minimal Cognitive Load:** Officers shouldn't need to mentally map Tamil names to geography (map solves this)
5. **Government Trust:** Professional typography, subtle shadows, clear hierarchy, no playful design elements
6. **Decision-Making UX:** Designed for action (call dealer, investigate region), not passive viewing
7. **Responsive First:** Works on tablets for field officers, full features on desktops for planners

---

## Next Steps

1. Implement React components matching these designs
2. Connect to FastAPI backend (6 endpoints + Phase 2 upgrades)
3. Add Plotly.js/D3 charts for data visualization
4. Integrate OpenLayers for map functionality
5. Build error boundaries and loading states
6. Test on mobile/tablet devices
7. Implement keyboard shortcuts for power users

---

**Design created:** March 29, 2026
**Framework:** Stitch AI Design System
**Target release:** Phase 1 (2 weeks) as React SPA
