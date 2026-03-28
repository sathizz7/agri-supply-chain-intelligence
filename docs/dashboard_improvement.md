# 🌾 TFAIS Dashboard Improvement Spec

> **Purpose**: Actionable improvement plan for the Streamlit dashboard. Each page is specified with exact chart types, data sources, Plotly patterns, and the API endpoints needed.  
> **Based on**: [Dashboard Critique](file:///C:/Users/FAI-Sathish/.gemini/antigravity/brain/bb5e4e6f-280b-4513-9d5e-7e9c35475f8d/dashboard_critique.md)

---

## Page Architecture: 5 → 7 Pages

```
CURRENT                              PROPOSED
─────────────────────                ─────────────────────
District Overview        ──────►     📍 Overview (redesigned)
                         ──────►     📊 Supply Matrix (NEW)
Stock Trends             ──────►     📉 Trends (enhanced)
Fertilizer Comparison    ──────►     🧪 Fertilizer Deep-Dive (enhanced)
Dealer Search            ──────►     🔍 Dealer Intel (enhanced)
Alerts                   ──────►     ⚠️ Alerts (redesigned)
                         ──────►     🧠 Supply Intelligence (NEW)
```

---

## Dependency: Switch from `st.bar_chart` to Plotly

**Every page below uses `plotly.express`**. This is the foundational change.

```python
# Add to imports at top of dashboard/app.py
import plotly.express as px
import plotly.graph_objects as go

# ALL st.bar_chart / st.line_chart calls → replaced with st.plotly_chart
```

No new `pip install` needed — Plotly ships with Streamlit.

---

## Page 1: 📍 Overview (Redesigned)

**Current**: 3 KPI cards + flat summary table + gray bar chart  
**Improved**: 4 KPI cards with deltas + color-coded bar chart + district heatmap table

### Layout

```
┌──────────────────────────────────────────────────────────┐
│  📍 OVERVIEW                                              │
│                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │Districts│  │ Dealers │  │  Stock  │  │⚠️Alerts │    │
│  │   38    │  │  4,200  │  │ 85.3T  │  │   42    │    │
│  │         │  │  ↑ 12   │  │ ↑3.2T  │  │  ↓ 8   │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  COLOR-CODED BAR CHART: Stock by District           │ │
│  │  🔴 low ───── 🟡 medium ───── 🟢 high              │ │
│  │  ██████████████████████████████████████             │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  SUMMARY TABLE with conditional formatting          │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### KPI Cards with Deltas

```python
# Requires: today's summary + yesterday's summary
today_summary = fetch_summary(date_str)
yesterday_str = str(selected_date - timedelta(days=1)) if selected_date else None
yesterday_summary = fetch_summary(yesterday_str) if yesterday_str else pd.DataFrame()

col1, col2, col3, col4 = st.columns(4)

# Districts
col1.metric("Districts", len(today_summary))

# Dealers (with delta)
today_dealers = int(today_summary["total_dealers"].sum()) if not today_summary.empty else 0
yest_dealers = int(yesterday_summary["total_dealers"].sum()) if not yesterday_summary.empty else 0
col2.metric("Total Dealers", today_dealers,
            delta=f"{today_dealers - yest_dealers:+d}" if yest_dealers else None)

# Stock (with delta)
today_stock = today_summary["total_stock_kg"].sum() / 1000 if not today_summary.empty else 0
yest_stock = yesterday_summary["total_stock_kg"].sum() / 1000 if not yesterday_summary.empty else 0
col3.metric("Total Stock (T)", f"{today_stock:.1f}",
            delta=f"{today_stock - yest_stock:+.1f}T" if yest_stock else None)

# Low-stock count
alerts_count = len(fetch_low_stock_count(date_str, low_stock_threshold))
col4.metric("⚠️ Low-Stock", alerts_count, delta_color="inverse")
```

**API change needed**: New endpoint `GET /summary/compare?date1=...&date2=...` or reuse existing `/summary?scrape_date=` with two calls.

### Color-Coded Bar Chart

```python
fig = px.bar(
    summary_df.sort_values("total_stock_kg", ascending=False),
    x="district_name",
    y="total_stock_kg",
    color="total_stock_kg",
    color_continuous_scale=["#e74c3c", "#f39c12", "#27ae60"],
    labels={"total_stock_kg": "Stock (kg)", "district_name": ""},
    title="District-wise Fertilizer Availability",
)
fig.update_layout(xaxis_tickangle=-45, height=450, plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, use_container_width=True)
```

---

## Page 2: 📊 Supply Matrix (NEW)

**Purpose**: District × Fertilizer heatmap — the single most powerful chart for this dataset. One glance shows exactly which district is short on which fertilizer.

### Layout

```
┌────────────────────────────────────────────────────────────┐
│  📊 SUPPLY MATRIX                                          │
│                                                            │
│              யூரியா  டிஏபி  பொட்டாஸ்  10-26-26  20-20-0   │
│  அரியலூர்    ██████  ██     ████      █         ███       │
│  செங்கல்பட்  ████    █████  ██████    ████      █████     │
│  ...                                                       │
│  (green = high stock, red = low stock, white = zero)       │
│                                                            │
│  ⚠️ 14 district-fertilizer combinations have ZERO stock   │
│                                                            │
│  ┌──────────────────────────────────────────────┐          │
│  │  ZERO-STOCK TABLE                            │          │
│  │  District        Fertilizer      Last Seen   │          │
│  │  அரியலூர்       பொட்டாஸ்       3 days ago  │          │
│  └──────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────┘
```

### Implementation

```python
elif page == "📊 Supply Matrix":
    st.title("📊 Supply Matrix: District × Fertilizer")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No data available.")
    else:
        # Pivot: district rows × fertilizer columns
        matrix = df.pivot_table(
            index="district_name",
            columns="fertilizer_name",
            values="quantity",
            aggfunc="sum",
            fill_value=0,
        )

        # Heatmap
        fig = px.imshow(
            matrix,
            labels=dict(x="Fertilizer", y="District", color="Stock (kg)"),
            color_continuous_scale="RdYlGn",
            aspect="auto",
        )
        fig.update_layout(height=max(400, len(matrix) * 25))
        st.plotly_chart(fig, use_container_width=True)

        # Zero-stock warning
        zero_mask = matrix == 0
        if zero_mask.any().any():
            st.warning(f"⚠️ {zero_mask.sum().sum()} district-fertilizer combinations have ZERO stock")

            # List the zero-stock pairs
            zeros_list = []
            for dist in matrix.index:
                for fert in matrix.columns:
                    if matrix.loc[dist, fert] == 0:
                        zeros_list.append({"District": dist, "Fertilizer": fert})

            st.dataframe(pd.DataFrame(zeros_list), use_container_width=True, hide_index=True)
```

**API change needed**: None — reuses existing `/fertilizer-stock` endpoint.

---

## Page 3: 📉 Trends (Enhanced)

**Current**: Single aggregated `st.line_chart`  
**Improved**: Multi-line Plotly chart + granularity selector + drill-down level

### Layout

```
┌──────────────────────────────────────────────────────────┐
│  📉 STOCK TRENDS                                          │
│                                                          │
│  Aggregation: [Daily] [Weekly] [Monthly]                 │
│  Drill-down:  [State Total] [By District] [By Block]     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │   Multi-line chart                                 │  │
│  │   — யூரியா (blue)                                  │  │
│  │   — டி ஏ பி (green)                                │  │
│  │   — பொட்டாஸ் (orange)                              │  │
│  │   [hover for exact values + date]                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │   Day-over-Day % Change Table                     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Implementation

```python
elif page == "📉 Trends":
    st.title("📉 Stock Trends Over Time")

    # Controls
    col1, col2 = st.columns(2)
    with col1:
        granularity = st.radio("Aggregation", ["Daily", "Weekly", "Monthly"], horizontal=True)
    with col2:
        level = st.radio("Drill-down", ["State Total", "By District"], horizontal=True)

    df = fetch_stock(district_code=selected_district_code)

    if df.empty:
        st.info("No stock data found.")
    else:
        df["date"] = pd.to_datetime(df["scrape_date"])

        # Resample based on granularity
        if granularity == "Weekly":
            df["period"] = df["date"].dt.to_period("W").dt.start_time
        elif granularity == "Monthly":
            df["period"] = df["date"].dt.to_period("M").dt.start_time
        else:
            df["period"] = df["date"]

        if level == "State Total":
            trend = df.groupby(["period", "fertilizer_name"])["quantity"].sum().reset_index()
            fig = px.line(
                trend, x="period", y="quantity", color="fertilizer_name",
                markers=True,
                labels={"quantity": "Stock (kg)", "period": "", "fertilizer_name": "Fertilizer"},
                title="State-wide Fertilizer Stock Trend",
            )
        else:
            trend = df.groupby(["period", "district_name", "fertilizer_name"])["quantity"].sum().reset_index()
            selected_fert = st.selectbox("Fertilizer", df["fertilizer_name"].unique())
            trend_filtered = trend[trend["fertilizer_name"] == selected_fert]
            fig = px.line(
                trend_filtered, x="period", y="quantity", color="district_name",
                markers=True,
                title=f"{selected_fert} — District Comparison",
            )

        fig.update_layout(height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # Day-over-day % change table
        if granularity == "Daily":
            st.subheader("Day-over-Day Change")
            pivot = df.groupby(["date", "fertilizer_name"])["quantity"].sum().unstack(fill_value=0)
            pct_change = pivot.pct_change().tail(7) * 100
            st.dataframe(
                pct_change.style.format("{:.1f}%").background_gradient(cmap="RdYlGn", axis=None),
                use_container_width=True,
            )
```

**API change needed**: Endpoint needs to support returning data across multiple dates (remove `scrape_date` filter or add `date_from`/`date_to` params).

---

## Page 4: 🧪 Fertilizer Deep-Dive (Enhanced)

**Current**: Bar chart of total by fertilizer + top dealers table  
**Improved**: Grouped bar chart by district + donut chart of share + top dealers

### Implementation

```python
elif page == "🧪 Fertilizer Deep-Dive":
    st.title("🧪 Fertilizer-wise Availability")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No data found.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Grouped bar: fertilizer breakdown by district
            grouped = df.groupby(["district_name", "fertilizer_name"])["quantity"].sum().reset_index()
            fig = px.bar(
                grouped,
                x="fertilizer_name", y="quantity", color="district_name",
                barmode="group",
                title="Fertilizer Stock by District",
                labels={"quantity": "Stock (kg)", "fertilizer_name": ""},
            )
            fig.update_layout(height=450, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Donut chart: share of total
            fert_totals = df.groupby("fertilizer_name")["quantity"].sum().reset_index()
            fig = px.pie(
                fert_totals, names="fertilizer_name", values="quantity",
                hole=0.4,
                title="Stock Share by Fertilizer",
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

        # Top dealers table
        st.subheader("Top 20 Dealers by Stock")
        top = (
            df.groupby(["dealer_name", "block_name", "district_name"])["quantity"]
            .sum().reset_index()
            .sort_values("quantity", ascending=False)
            .head(20)
        )
        st.dataframe(top, use_container_width=True, hide_index=True)
```

---

## Page 5: 🔍 Dealer Intel (Enhanced)

**Current**: Code search + flat stock history table  
**Improved**: Code search + stock history line chart + per-fertilizer sparklines

### Key Addition — Stock History Chart

```python
# After showing dealer details...
if result.get("stock_history"):
    st.subheader("Stock History")
    hist_df = pd.DataFrame(result["stock_history"])
    hist_df["scrape_date"] = pd.to_datetime(hist_df["scrape_date"])

    fig = px.line(
        hist_df, x="scrape_date", y="quantity",
        color="fertilizer_name",
        markers=True,
        title=f"Stock Trend: {result['name_ta']}",
        labels={"quantity": "Stock (kg)", "scrape_date": ""},
    )
    fig.update_layout(height=350, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # Also show the table for raw data
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
```

---

## Page 6: ⚠️ Alerts (Redesigned)

**Current**: Flat table filtered by threshold  
**Improved**: 3-tier severity cards + treemap + sortable table

### Layout

```
┌──────────────────────────────────────────────────────────┐
│  ⚠️ LOW-STOCK ALERTS                                     │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │🔴Critical│  │🟡Warning │  │🟠Caution │               │
│  │  < 100kg │  │ < 300kg  │  │ < 500kg  │               │
│  │ 42 items │  │ 128 items│  │ 230 items│               │
│  └──────────┘  └──────────┘  └──────────┘               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  TREEMAP: visual area = stock deficit              │  │
│  │  ┌────────┬───────────────┐                        │  │
│  │  │District │  District B  │                        │  │
│  │  │  A     │  ┌─────┬────┐│                        │  │
│  │  │┌─────┐│  │Deal1│  D2││                        │  │
│  │  ││Deal1 ││  └─────┴────┘│                        │  │
│  │  │└─────┘│               │                        │  │
│  │  └────────┴───────────────┘                        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  DETAILED TABLE (sortable, filterable)             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Implementation

```python
elif page == "⚠️ Alerts":
    st.title("⚠️ Low-Stock Alerts")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No data available.")
    else:
        latest = df.sort_values("scrape_date").groupby(
            ["dealer_code", "fertilizer_name"]
        ).last().reset_index()

        alerts = latest[latest["quantity"] < low_stock_threshold].copy()

        if alerts.empty:
            st.success(f"✅ No dealers below {low_stock_threshold} kg — supply looks adequate!")
        else:
            # Severity tiers
            alerts["severity"] = pd.cut(
                alerts["quantity"],
                bins=[-1, 100, 300, low_stock_threshold],
                labels=["🔴 Critical (<100kg)", "🟡 Warning (<300kg)", "🟠 Caution"]
            )

            # Severity cards
            cols = st.columns(3)
            for i, (sev, group) in enumerate(alerts.groupby("severity", observed=True)):
                cols[i].metric(str(sev), f"{len(group)} dealer-fertilizer pairs")

            st.divider()

            # Treemap
            st.subheader("Alert Distribution")
            fig = px.treemap(
                alerts,
                path=["severity", "district_name", "dealer_name"],
                values="quantity",
                color="quantity",
                color_continuous_scale="RdYlGn",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            st.subheader("Alert Details")
            st.dataframe(
                alerts[["severity", "district_name", "block_name",
                        "dealer_name", "fertilizer_name", "quantity"]]
                .sort_values("quantity")
                .rename(columns={
                    "district_name": "District", "block_name": "Block",
                    "dealer_name": "Dealer", "fertilizer_name": "Fertilizer",
                    "quantity": "Stock (kg)", "severity": "Severity",
                }),
                use_container_width=True, hide_index=True,
            )
```

---

## Page 7: 🧠 Supply Intelligence (NEW)

**Purpose**: Answer questions a data analyst would ask — concentration risk, coverage gaps, volatility.

### 3 Tabs

```python
elif page == "🧠 Intelligence":
    st.title("🧠 Supply Intelligence")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No data available.")
    else:
        tab1, tab2, tab3 = st.tabs([
            "📊 Stock Concentration",
            "🕳️ Coverage Gaps",
            "📈 Stock Volatility"
        ])
```

#### Tab 1: Stock Concentration

_"Are 3 dealers holding 80% of the Urea in this district?"_ — monopoly risk.

```python
        with tab1:
            st.subheader("Stock Concentration by District")
            st.caption("Shows what % of a fertilizer's stock is held by the top-N dealers")

            selected_fert = st.selectbox("Select Fertilizer", df["fertilizer_name"].unique())
            fert_df = df[df["fertilizer_name"] == selected_fert]

            for dist_name, dist_group in fert_df.groupby("district_name"):
                total = dist_group["quantity"].sum()
                if total == 0:
                    continue

                top5 = dist_group.nlargest(5, "quantity")
                top5_pct = top5["quantity"].sum() / total * 100

                color = "🔴" if top5_pct > 80 else "🟡" if top5_pct > 60 else "🟢"
                with st.expander(f"{color} {dist_name} — Top 5 hold {top5_pct:.0f}%"):
                    fig = px.pie(
                        top5, names="dealer_name", values="quantity",
                        title=f"{selected_fert} distribution in {dist_name}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
```

#### Tab 2: Coverage Gaps

_"Which blocks have ZERO stock of DAP?"_ — supply desert detection.

```python
        with tab2:
            st.subheader("🕳️ Coverage Gaps")
            st.caption("Blocks where a fertilizer has zero stock")

            # All possible (block, fertilizer) pairs vs what actually has stock
            all_blocks = df[["block_name", "district_name"]].drop_duplicates()
            all_ferts = df["fertilizer_name"].unique()
            all_combos = pd.MultiIndex.from_product(
                [all_blocks["block_name"], all_ferts], names=["block_name", "fertilizer_name"]
            ).to_frame(index=False)

            stocked = df[df["quantity"] > 0].groupby(
                ["block_name", "fertilizer_name"]
            ).size().reset_index(name="count")

            gaps = all_combos.merge(stocked, how="left", on=["block_name", "fertilizer_name"])
            gaps = gaps[gaps["count"].isna()].drop(columns="count")
            gaps = gaps.merge(all_blocks, on="block_name")

            if gaps.empty:
                st.success("✅ All blocks have stock for all fertilizer types")
            else:
                st.warning(f"⚠️ {len(gaps)} block-fertilizer gaps detected")

                # Group by fertilizer for readability
                for fert, group in gaps.groupby("fertilizer_name"):
                    with st.expander(f"❌ {fert} — missing in {len(group)} blocks"):
                        st.dataframe(group[["district_name", "block_name"]],
                                     use_container_width=True, hide_index=True)
```

#### Tab 3: Stock Volatility

_"Which dealers' stock swings wildly day-to-day?"_ — unstable supply chain indicator.

```python
        with tab3:
            st.subheader("📈 Stock Volatility")
            st.caption("Dealers with highest day-to-day stock variance (needs multi-day data)")

            # Need multi-day data for this
            multi_df = fetch_stock(district_code=selected_district_code)  # no date filter

            if multi_df.empty or multi_df["scrape_date"].nunique() < 2:
                st.info("Need data from multiple scrape dates to calculate volatility")
            else:
                vol = (
                    multi_df.groupby(["dealer_name", "district_name", "fertilizer_name"])
                    ["quantity"].agg(["mean", "std", "count"])
                    .reset_index()
                )
                vol["cv"] = (vol["std"] / vol["mean"] * 100).fillna(0)  # coefficient of variation
                vol = vol[vol["count"] >= 3]  # need at least 3 data points
                vol = vol.sort_values("cv", ascending=False).head(20)

                fig = px.bar(
                    vol, x="dealer_name", y="cv",
                    color="cv", color_continuous_scale="YlOrRd",
                    hover_data=["district_name", "fertilizer_name", "mean", "std"],
                    title="Top 20 Most Volatile Dealers (Coefficient of Variation %)",
                    labels={"cv": "Volatility %", "dealer_name": ""},
                )
                fig.update_layout(xaxis_tickangle=-45, height=450)
                st.plotly_chart(fig, use_container_width=True)
```

---

## API Endpoints Needed

| Endpoint | Exists? | Needed By |
|---|---|---|
| `GET /districts` | ✅ | All pages |
| `GET /summary` | ✅ | Overview |
| `GET /fertilizer-stock` | ✅ | All chart pages |
| `GET /dealer-details` | ✅ | Dealer Intel |
| `GET /fertilizer-stock?date_from=&date_to=` | ❌ New params | Trends, Volatility |
| `GET /scrape-runs` | ❌ New | Scrape Status (future) |

Only 1 API change is strictly needed — adding `date_from`/`date_to` filter params to `/fertilizer-stock`.

---

## Implementation Order

| Phase | Pages | Effort | Impact |
|---|---|---|---|
| **Phase A**: Plotly foundation | Switch all existing charts to Plotly | 2 hrs | High — everything looks better |
| **Phase B**: KPI + Alerts redesign | Overview deltas + Alert severity tiers | 2 hrs | High — actionable intelligence |
| **Phase C**: Supply Matrix | New page — heatmap | 2 hrs | Very high — single best visualization |
| **Phase D**: Trends + Deep-Dive | Granularity selector + grouped bars + donut | 3 hrs | Medium — power user features |
| **Phase E**: Dealer Intel | Stock history chart | 1 hr | Medium — per-dealer insight |
| **Phase F**: Intelligence | Concentration + Gaps + Volatility | 4 hrs | High — decision-support layer |

**Total: ~14 hours of implementation across 6 phases.**

---

## Sidebar Update

```python
page = st.sidebar.radio(
    "View",
    [
        "📍 Overview",
        "📊 Supply Matrix",
        "📉 Trends",
        "🧪 Fertilizer Deep-Dive",
        "🔍 Dealer Intel",
        "⚠️ Alerts",
        "🧠 Intelligence",
    ],
)
```

---

## File Changes Summary

| File | Change Type |
|---|---|
| `dashboard/app.py` | Major rewrite — add Plotly, restructure into 7 pages |
| `tfais/api/main.py` | Minor — add `date_from`/`date_to` params to `/fertilizer-stock` |
| `assets/tn_districts.geojson` | New — Tamil Nadu district boundaries (for future map) |
| `requirements.txt` | No change — Plotly ships with Streamlit |
