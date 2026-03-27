# 🌾 Project Title

**Tamil Nadu Fertilizer Availability Intelligence System (TFAIS)**

---

# 🎯 Problem Statement

The Tamil Nadu government fertilizer portal provides  **district-wise and circle-wise fertilizer stock data** , but:

* Data is **deeply nested (state → district → block → dealer)**
* Not machine-readable (HTML tables, no API)
* No historical tracking
* No analytics or forecasting capability

👉 This makes it hard to:

* Monitor shortages
* Analyze distribution inefficiencies
* Build farmer-facing insights

---

# 🚀 Project Goal

To build an **end-to-end data pipeline + analytics dashboard** that:

1. Scrapes fertilizer availability data **without loss of tabular structure**
2. Stores it in a **normalized + query-efficient database**
3. Enables **real-time monitoring + historical analysis**
4. Powers a **dashboard for decision-making**

---

# 🧩 Core System Architecture

### 1. Data Ingestion Layer

* Input: Target site

  `http://115.243.209.84/...`

* Scraping levels:
* State → District → Block → Dealer
* Extract:
* Fertilizer type (e.g., Urea, DAP, 16-16-16)
* Quantity available
* Dealer details
* Contact info

👉 Key requirement: **Preserve exact table hierarchy (no flattening loss)**

---

### 2. Parsing & Structuring Layer

Convert raw HTML tables into structured format:

**Raw (HTML Table) → Structured JSON**

Example:

<pre class="overflow-visible! px-0!" data-start="1615" data-end="1833"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>{</span><br/><span>  "district": </span><span class="ͼr">"Thanjavur"</span><span>,</span><br/><span>  "block": </span><span class="ͼr">"Thirukattupalli"</span><span>,</span><br/><span>  "dealer_name": </span><span class="ͼr">"XYZ Agro"</span><span>,</span><br/><span>  "fertilizers": {</span><br/><span>    "DAP": </span><span class="ͼq">1650</span><span>,</span><br/><span>    "16-16-16": </span><span class="ͼq">6500</span><br/><span>  },</span><br/><span>  "contact": </span><span class="ͼr">"9841713690"</span><span>,</span><br/><span>  "timestamp": </span><span class="ͼr">"2026-03-18"</span><br/><span>}</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

### 3. Storage Layer

#### Recommended Hybrid Storage:

**1. Relational DB (PostgreSQL)**

* District
* Block
* Dealer
* Fertilizer stock

**2. Optional: Data Warehouse / OLAP**

* For trends & analytics

**Schema Design (Core Tables)**

* `districts`
* `blocks`
* `dealers`
* `fertilizer_stock`
* `scrape_metadata`

👉 Key design goal:

**Support time-series + geo-hierarchy queries**

---

### 4. Data Processing Layer

* Data validation (missing values, duplicates)
* Change detection (stock updates)
* Aggregations:
* District-level stock
* Fertilizer-wise availability
* Alerts:
* Low stock detection

---

### 5. API Layer

Expose structured endpoints:

* `/districts`
* `/blocks?district=...`
* `/fertilizer-stock?district=...`
* `/dealer-details`

---

### 6. Dashboard Layer

Frontend (Streamlit / React):

**Key Features**

* 📍 District-wise availability map
* 📊 Fertilizer-wise comparison
* 📉 Stock trends over time
* ⚠️ Low-stock alerts
* 📞 Dealer contact access

---

# 📥 Input

### Source

* Government fertilizer website (HTML tables)

### Data Type

* Semi-structured tabular data

### Frequency

* Daily / Scheduled scraping

---

# 📤 Output

### 1. Structured Database

* Clean, normalized fertilizer availability data

### 2. APIs

* Queryable endpoints for frontend

### 3. Dashboard

* Visual analytics for:
* Policymakers
* Agricultural officers
* Farmers (future scope)

---

# 📊 Expected Outcomes

* ✅ Centralized fertilizer intelligence system
* ✅ Improved supply chain visibility
* ✅ Early shortage detection
* ✅ Data-driven agricultural planning
* ✅ Foundation for predictive analytics

---

# ⚠️ Key Challenges (Important for Interview / Pitch)

### 1. Nested Scraping Complexity

* Multi-level navigation (district → block → dealer)

### 2. Data Consistency

* Same dealer appearing multiple times
* Missing values / inconsistent formats

### 3. Change Detection

* Need to track **delta updates** over time

### 4. No API Dependency

* Must rely on **robust scraping logic**

# 🧪 Success Metrics

* Data completeness (% of fields captured)
* Scraping reliability (failure rate)
* Query latency (API performance)
* Dashboard usability

---

# 💡 One-line Pitch

> “Built an end-to-end intelligent system that transforms Tamil Nadu’s static fertilizer availability website into a real-time, queryable, and analytics-driven platform for agricultural decision-making.”
>
