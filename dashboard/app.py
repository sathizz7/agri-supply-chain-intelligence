"""
Phase 6: Streamlit Dashboard (Improved with Plotly)

7-Page Layout:
  1. 📍 Overview      - KPI metrics + color-coded bar chart + summary table
  2. 📊 Supply Matrix - District × Fertilizer heatmap + zero-stock warnings
  3. 📉 Trends        - Multi-line trends with granularity + day-over-day change
  4. 🧪 Deep-Dive     - Grouped bars by district + donut chart + top dealers
  5. 🔍 Dealer Intel  - Stock history line chart + dealer search
  6. ⚠️ Alerts         - Severity tiers + treemap + sortable table
  7. 🧠 Intelligence  - Concentration risk + coverage gaps + volatility

Run: streamlit run dashboard/app.py
"""
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = os.getenv("TFAIS_API_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TFAIS Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def fetch_districts() -> list[dict]:
    try:
        r = requests.get(f"{API_BASE}/districts", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Could not reach API: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_summary(scrape_date: str | None = None) -> pd.DataFrame:
    params = {}
    if scrape_date:
        params["scrape_date"] = scrape_date
    try:
        r = requests.get(f"{API_BASE}/summary", params=params, timeout=10)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_stock(
    district_code: str | None = None,
    block_code: str | None = None,
    scrape_date: str | None = None,
) -> pd.DataFrame:
    params = {"limit": 2000}
    if district_code:
        params["district_code"] = district_code
    if block_code:
        params["block_code"] = block_code
    if scrape_date:
        params["scrape_date"] = scrape_date
    try:
        r = requests.get(f"{API_BASE}/fertilizer-stock", params=params, timeout=15)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        if not df.empty:
            df["scrape_date"] = pd.to_datetime(df["scrape_date"])
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_dealer(dealer_code: str) -> dict | None:
    try:
        r = requests.get(
            f"{API_BASE}/dealer-details",
            params={"dealer_code": dealer_code},
            timeout=10,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------------------------

st.sidebar.title("🌾 TFAIS")
st.sidebar.caption("Tamil Nadu Fertilizer Availability Intelligence System")
st.sidebar.divider()

page = st.sidebar.radio(
    "View",
    [
        "📍 Overview",
        "📊 Supply Matrix",
        "📉 Trends",
        "🧪 Deep-Dive",
        "🔍 Dealer Intel",
        "⚠️ Alerts",
        "🧠 Intelligence",
    ],
)

# Date filter
selected_date = st.sidebar.date_input("Scrape date", value=None)
date_str = str(selected_date) if selected_date else None

# District filter
districts = fetch_districts()
district_options = {d["name_ta"]: d["code"] for d in districts}
selected_district_name = st.sidebar.selectbox(
    "District", ["All"] + list(district_options.keys())
)
selected_district_code = (
    district_options[selected_district_name]
    if selected_district_name != "All"
    else None
)

# Low-stock threshold
low_stock_threshold = st.sidebar.number_input(
    "Low-stock alert threshold (kg)", min_value=0, value=500, step=100
)

# ---------------------------------------------------------------------------
# Page 1: Overview (KPI + Color-Coded Bar + Summary Table)
# ---------------------------------------------------------------------------

if page == "📍 Overview":
    st.title("📍 District-wise Fertilizer Availability")

    summary_df = fetch_summary(date_str)

    if summary_df.empty:
        st.info("No data available. Run the scraper first: `python main.py`")
    else:
        # KPI Cards with deltas
        col1, col2, col3, col4 = st.columns(4)

        today_summary = fetch_summary(date_str)
        # Calculate yesterday for delta
        if selected_date:
            yesterday = selected_date - timedelta(days=1)
            yesterday_str = str(yesterday)
            yesterday_summary = fetch_summary(yesterday_str)
        else:
            yesterday_summary = pd.DataFrame()

        col1.metric("Districts", len(today_summary))

        today_dealers = int(today_summary["total_dealers"].sum()) if not today_summary.empty else 0
        yest_dealers = int(yesterday_summary["total_dealers"].sum()) if not yesterday_summary.empty else 0
        col2.metric("Total Dealers", today_dealers,
                    delta=f"{today_dealers - yest_dealers:+d}" if yest_dealers else None)

        today_stock = today_summary["total_stock_kg"].sum() / 1000 if not today_summary.empty else 0
        yest_stock = yesterday_summary["total_stock_kg"].sum() / 1000 if not yesterday_summary.empty else 0
        col3.metric("Total Stock (T)", f"{today_stock:.1f}",
                    delta=f"{today_stock - yest_stock:+.1f}T" if yest_stock else None)

        col4.metric("⚠️ Low-Stock", "—", help="Enable on Alerts page")

        st.divider()

        # Color-coded bar chart
        st.subheader("Stock by District (Color = Availability)")
        summary_sorted = summary_df.sort_values("total_stock_kg", ascending=False)
        fig = px.bar(
            summary_sorted,
            x="district_name",
            y="total_stock_kg",
            color="total_stock_kg",
            color_continuous_scale=["#e74c3c", "#f39c12", "#27ae60"],  # red → yellow → green
            labels={"total_stock_kg": "Stock (kg)", "district_name": ""},
            title="",
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=450,
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        st.subheader("District Summary Table")
        display_df = summary_df.rename(columns={
            "district_name": "District",
            "total_dealers": "Dealers",
            "total_stock_kg": "Total Stock (kg)",
            "last_scraped": "Last Scraped",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Page 2: Supply Matrix (District × Fertilizer Heatmap)
# ---------------------------------------------------------------------------

elif page == "📊 Supply Matrix":
    st.title("📊 Supply Matrix: District × Fertilizer")
    st.caption("Heatmap showing which fertilizers are available in which districts")

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
            zero_count = zero_mask.sum().sum()
            st.warning(f"⚠️ {zero_count} district-fertilizer combinations have ZERO stock")

            # List the zero-stock pairs
            zeros_list = []
            for dist in matrix.index:
                for fert in matrix.columns:
                    if matrix.loc[dist, fert] == 0:
                        zeros_list.append({"District": dist, "Fertilizer": fert})

            st.dataframe(pd.DataFrame(zeros_list), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Page 3: Trends (Multi-line with Granularity + Day-over-Day)
# ---------------------------------------------------------------------------

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
        df["date"] = df["scrape_date"]

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
            col1, col2 = st.columns([3, 1])
            with col2:
                selected_fert = st.selectbox("Fertilizer", df["fertilizer_name"].unique())
            trend_filtered = trend[trend["fertilizer_name"] == selected_fert]
            fig = px.line(
                trend_filtered, x="period", y="quantity", color="district_name",
                markers=True,
                title=f"{selected_fert} — District Comparison",
            )

        fig.update_layout(height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # Day-over-day % change
        if granularity == "Daily":
            st.subheader("Day-over-Day Change (%)")
            pivot = df.groupby(["date", "fertilizer_name"])["quantity"].sum().unstack(fill_value=0)
            pct_change = pivot.pct_change().tail(7) * 100
            st.dataframe(
                pct_change.style.format("{:.1f}%").background_gradient(cmap="RdYlGn", axis=None),
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Page 4: Deep-Dive (Grouped Bars + Donut + Top Dealers)
# ---------------------------------------------------------------------------

elif page == "🧪 Deep-Dive":
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


# ---------------------------------------------------------------------------
# Page 5: Dealer Intel (Search + Stock History Chart)
# ---------------------------------------------------------------------------

elif page == "🔍 Dealer Intel":
    st.title("🔍 Dealer Contact & Stock Intelligence")

    col1, col2 = st.columns([2, 1])
    with col1:
        dealer_code_input = st.text_input("Enter dealer code (e.g. 999210)")
    with col2:
        search_btn = st.button("Search", type="primary")

    if search_btn and dealer_code_input:
        result = fetch_dealer(dealer_code_input.strip())
        if result is None:
            st.error(f"Dealer '{dealer_code_input}' not found.")
        else:
            st.subheader(result["name_ta"])
            col1, col2, col3 = st.columns(3)
            col1.metric("Block", result.get("block_name", "—"))
            col2.metric("District", result.get("district_name", "—"))
            col3.metric("Contact", result.get("contact") or "—")

            if result.get("address"):
                st.caption(f"Address: {result['address']}")

            if result.get("stock_history"):
                st.subheader("Stock History")
                hist_df = pd.DataFrame(result["stock_history"])
                hist_df["scrape_date"] = pd.to_datetime(hist_df["scrape_date"])

                # Line chart: stock history over time
                fig = px.line(
                    hist_df, x="scrape_date", y="quantity",
                    color="fertilizer_name",
                    markers=True,
                    title=f"Stock Trend: {result['name_ta']}",
                    labels={"quantity": "Stock (kg)", "scrape_date": ""},
                )
                fig.update_layout(height=350, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

                # Table for raw data
                st.dataframe(hist_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Browse Dealers by Block")
    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)
    if not df.empty:
        dealer_list = (
            df[["dealer_code", "dealer_name", "block_name", "district_name", "contact"]]
            .drop_duplicates(subset=["dealer_code"])
            .reset_index(drop=True)
        )
        if "contact" not in dealer_list.columns:
            dealer_list["contact"] = "—"
        st.dataframe(dealer_list, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Page 6: Alerts (Severity Tiers + Treemap + Table)
# ---------------------------------------------------------------------------

elif page == "⚠️ Alerts":
    st.title("⚠️ Low-Stock Alerts")
    st.caption(f"Dealers with any fertilizer below {low_stock_threshold} kg")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No stock data available.")
    else:
        latest = df.sort_values("scrape_date").groupby(
            ["dealer_code", "fertilizer_name"]
        ).last().reset_index()

        alerts = latest[latest["quantity"] < low_stock_threshold].copy()

        if alerts.empty:
            st.success(
                f"✅ No dealers below {low_stock_threshold} kg. "
                "Supply looks adequate!"
            )
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
                if i < 3:
                    cols[i].metric(str(sev), f"{len(group)} pairs")

            st.divider()

            # Treemap: alert distribution
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
                alerts[[
                    "severity", "district_name", "block_name",
                    "dealer_name", "fertilizer_name", "quantity"
                ]]
                .sort_values("quantity")
                .rename(columns={
                    "district_name": "District", "block_name": "Block",
                    "dealer_name": "Dealer", "fertilizer_name": "Fertilizer",
                    "quantity": "Stock (kg)", "severity": "Severity",
                }),
                use_container_width=True, hide_index=True,
            )


# ---------------------------------------------------------------------------
# Page 7: Intelligence (Concentration + Gaps + Volatility)
# ---------------------------------------------------------------------------

elif page == "🧠 Intelligence":
    st.title("🧠 Supply Intelligence")
    st.caption("Data-driven insights for supply chain decision-making")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No data available.")
    else:
        tab1, tab2, tab3 = st.tabs([
            "📊 Stock Concentration",
            "🕳️ Coverage Gaps",
            "📈 Stock Volatility"
        ])

        # Tab 1: Concentration Risk
        with tab1:
            st.subheader("Stock Concentration by District")
            st.caption("Shows what % of a fertilizer's stock is held by the top-5 dealers (monopoly risk)")

            selected_fert = st.selectbox("Select Fertilizer", df["fertilizer_name"].unique(), key="conc_fert")
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

        # Tab 2: Coverage Gaps
        with tab2:
            st.subheader("🕳️ Coverage Gaps")
            st.caption("Blocks where a fertilizer has zero stock")

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

                for fert, group in gaps.groupby("fertilizer_name"):
                    with st.expander(f"❌ {fert} — missing in {len(group)} blocks"):
                        st.dataframe(group[["district_name", "block_name"]],
                                     use_container_width=True, hide_index=True)

        # Tab 3: Volatility
        with tab3:
            st.subheader("📈 Stock Volatility")
            st.caption("Dealers with highest day-to-day stock variance (needs multi-day data)")

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

                if vol.empty:
                    st.info("Insufficient data points for volatility calculation")
                else:
                    fig = px.bar(
                        vol, x="dealer_name", y="cv",
                        color="cv", color_continuous_scale="YlOrRd",
                        hover_data=["district_name", "fertilizer_name", "mean", "std"],
                        title="Top 20 Most Volatile Dealers (Coefficient of Variation %)",
                        labels={"cv": "Volatility %", "dealer_name": ""},
                    )
                    fig.update_layout(xaxis_tickangle=-45, height=450)
                    st.plotly_chart(fig, use_container_width=True)
