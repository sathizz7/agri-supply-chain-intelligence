"""
Phase 6: Streamlit Dashboard

Features:
  - District-wise availability map
  - Fertilizer-wise comparison bar charts
  - Stock trends over time
  - Low-stock alerts
  - Dealer contact search

Run: streamlit run dashboard/app.py
"""
import os

import pandas as pd
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
            df["scraped_at"] = pd.to_datetime(df["scraped_at"])
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
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("🌾 TFAIS")
st.sidebar.caption("Tamil Nadu Fertilizer Availability Intelligence System")
st.sidebar.divider()

page = st.sidebar.radio(
    "View",
    ["District Overview", "Stock Trends", "Fertilizer Comparison", "Dealer Search", "Alerts"],
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
# Pages
# ---------------------------------------------------------------------------

if page == "District Overview":
    st.title("📍 District-wise Fertilizer Availability")

    summary_df = fetch_summary(date_str)

    if summary_df.empty:
        st.info("No data available. Run the scraper first: `python main.py`")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Districts", len(summary_df))
        col2.metric("Total Dealers", int(summary_df["total_dealers"].sum()))
        col3.metric(
            "Total Stock (tonnes)",
            f"{summary_df['total_stock_kg'].sum() / 1000:.1f}",
        )

        st.divider()
        st.subheader("District Summary Table")
        display_df = summary_df.rename(columns={
            "district_name": "District",
            "total_dealers": "Dealers",
            "total_stock_kg": "Total Stock (kg)",
            "last_scraped": "Last Scraped",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.subheader("Stock by District")
        chart_df = summary_df.set_index("district_name")["total_stock_kg"].sort_values(
            ascending=False
        )
        st.bar_chart(chart_df)


elif page == "Stock Trends":
    st.title("📉 Stock Trends Over Time")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No stock data found for the selected filters.")
    else:
        df["date"] = df["scraped_at"].dt.date
        trend_df = (
            df.groupby(["date", "fertilizer_name"])["quantity_kg"]
            .sum()
            .reset_index()
            .pivot(index="date", columns="fertilizer_name", values="quantity_kg")
            .fillna(0)
        )
        st.line_chart(trend_df)

        st.caption(
            f"Showing aggregated stock for "
            f"{'all districts' if not selected_district_code else selected_district_name}"
        )


elif page == "Fertilizer Comparison":
    st.title("📊 Fertilizer-wise Availability")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No stock data found for the selected filters.")
    else:
        fert_totals = (
            df.groupby("fertilizer_name")["quantity_kg"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(fert_totals)

        st.subheader("Top Dealers by Stock")
        dealer_totals = (
            df.groupby(["dealer_name", "block_name", "district_name"])["quantity_kg"]
            .sum()
            .reset_index()
            .sort_values("quantity_kg", ascending=False)
            .head(20)
        )
        st.dataframe(dealer_totals, use_container_width=True, hide_index=True)


elif page == "Dealer Search":
    st.title("📞 Dealer Contact Search")

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
                hist_df["scraped_at"] = pd.to_datetime(hist_df["scraped_at"])
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


elif page == "Alerts":
    st.title("⚠️ Low-Stock Alerts")
    st.caption(f"Dealers with any fertilizer below {low_stock_threshold} kg")

    df = fetch_stock(district_code=selected_district_code, scrape_date=date_str)

    if df.empty:
        st.info("No stock data available.")
    else:
        latest = df.sort_values("scraped_at").groupby(
            ["dealer_code", "fertilizer_name"]
        ).last().reset_index()

        alerts = latest[latest["quantity_kg"] < low_stock_threshold].copy()
        alerts = alerts.sort_values("quantity_kg")

        if alerts.empty:
            st.success(
                f"No dealers below {low_stock_threshold} kg threshold. "
                "Supply looks adequate!"
            )
        else:
            st.warning(f"{len(alerts)} low-stock records found")
            st.dataframe(
                alerts[[
                    "district_name", "block_name", "dealer_name",
                    "fertilizer_name", "quantity_kg", "scraped_at"
                ]].rename(columns={
                    "district_name": "District",
                    "block_name": "Block",
                    "dealer_name": "Dealer",
                    "fertilizer_name": "Fertilizer",
                    "quantity_kg": "Stock (kg)",
                    "scraped_at": "Last Scraped",
                }),
                use_container_width=True,
                hide_index=True,
            )
