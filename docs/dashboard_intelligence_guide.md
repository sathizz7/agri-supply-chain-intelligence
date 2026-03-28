# 7-Page Dashboard: Intelligence Guide

Quick reference for what insights each page reveals and who should use it.

---

## 📍 **Overview** — The Big Picture

### What It Shows
- **At a glance**: Total districts (38), total dealers (~4,200), total stock (T), low-stock count
- **Day-over-day**: How many new dealers were added, stock gained/lost since yesterday
- **Per-district**: Ranking of districts by stock level (color-coded: red/yellow/green)

### Who Uses It
- **Supply chain managers** — Daily morning briefing
- **Policy makers** — State-level capacity overview
- **Stakeholders** — Executive summary

### Key Questions Answered
- "How much fertilizer stock does TN have right now?"
- "Is supply going up or down since yesterday?"
- "Which districts are well-stocked vs struggling?"

### Action Triggers
- 🔴 If total stock is RED (low): Emergency allocation needed
- 📉 If delta is negative: Investigate why stock is declining
- 🔍 Click a district to drill into Supply Matrix

---

## 📊 **Supply Matrix** — Coverage & Gaps

### What It Shows
- **Heatmap**: Every district (rows) × every fertilizer type (columns)
  - Green = high stock, Red = zero/low stock
- **Zero-stock table**: Explicit list of (district, fertilizer) pairs with NO stock
- **At-a-glance**: Can you get DAP in Tirunelveli? No, it's red.

### Who Uses It
- **Field agents** — "Can I recommend this fertilizer to this district?"
- **Logistics** — "Where do we need emergency shipments?"
- **Regional coordinators** — "Which areas have coverage gaps?"

### Key Questions Answered
- "Which fertilizers are unavailable in which districts?"
- "How many fertilizer-district combinations have zero stock?" (e.g., 14 gaps = problem)
- "Is there a pattern? (e.g., Urea everywhere, DAP nowhere)"

### Action Triggers
- 🔴 >10 zero-stock pairs: Major supply crisis
- 📍 Specific gaps repeated weekly: Need permanent sourcing solution
- ✓ All green: Supply chain is healthy

---

## 📉 **Trends** — Temporal Patterns

### What It Shows
- **Multi-line chart**: How stock of each fertilizer changed over time
- **Granularity**: View by day, week, or month
- **Drill-down**: Overall state trends vs per-district trends
- **% change**: Day-over-day percentage swings (e.g., +12%, -8%)

### Who Uses It
- **Trend analysts** — "Is demand recovering?"
- **Seasonal planners** — "When do we usually run low?"
- **Finance** — "What's the velocity of stock consumption?"

### Key Questions Answered
- "Is DAP stock recovering after the shortage last month?"
- "Which fertilizer is most volatile?"
- "Are we heading into a surplus or deficit?"
- "Is Thanjavur's supply stable or swinging wildly?"

### Action Triggers
- 📈 Upward trend: Good, supply catching up with demand
- 📉 Downward trend >10%/day: Unsustainable, stock will run out
- 📊 Seasonal patterns: Plan rotations accordingly
- ⚠️ Sharp drops: Investigate why (distributor issue? demand spike?)

---

## 🧪 **Deep-Dive** — Product & Dealer Analysis

### What It Shows
- **Grouped bar chart**: Stock of each fertilizer, broken down by district
  - "How much Urea in each district?" (side-by-side comparison)
- **Donut chart**: What % of total stock is each fertilizer?
  - "Urea = 40%, DAP = 35%, others = 25%"
- **Top 20 dealers**: Which shops are holding the most stock?

### Who Uses It
- **Procurement** — "Do we have enough of each fertilizer?"
- **Dealers** — "How do I compare to other dealers?"
- **Inventory managers** — "Which products are over/under-stocked?"

### Key Questions Answered
- "How is Urea distributed across districts? (fair or concentrated?)"
- "Is DAP availability balanced or skewed?"
- "Which 3 dealers hold 50% of all fertilizer?"
- "Do all districts have access to all fertilizer types?"

### Action Triggers
- 📊 Donut is imbalanced (e.g., 1 fertilizer = 70%): Over-reliance risk
- 🏪 Top 3 dealers = 80% of stock: Dealer concentration risk (if one fails, crisis)
- 📍 1 district dominates in a fertilizer: Consider redistribution
- 🔄 Unequal distribution: Suggests supply chain inefficiency

---

## 🔍 **Dealer Intel** — Granular & Historical

### What It Shows
- **Search**: Find any dealer by code, see their profile (name, address, phone)
- **Stock history**: Line chart of this dealer's inventory over time
  - See if they're reliable, if they're restocking
- **Browse table**: All dealers in your selected district (searchable, sortable)
- **Contact info**: Immediately call or visit if needed

### Who Uses It
- **Field coordinators** — "Can I buy from dealer #364468?"
- **Logistics** — "Has this dealer been restocking regularly?"
- **Farmers** — "Where's the nearest shop with Urea?"
- **Quality control** — "Track this dealer's stock patterns"

### Key Questions Answered
- "Who is dealer 364468 and what's their contact?"
- "Has this dealer been reliable (steady stock) or flaky (ups & downs)?"
- "When was the last time this dealer restocked?"
- "Are there other dealers in this block I can approach?"

### Action Triggers
- 📞 Stock history flat for weeks: Dealer is out of business / not replenishing
- 📈 Stock spikes then drops: Good sign of regular restocking
- 🔴 Zero stock for >7 days: Contact dealer, offer supplies
- ✓ Steady upward trend: Trusted partner, can rely on them

---

## ⚠️ **Alerts** — Risk & Response

### What It Shows
- **Severity cards**:
  - 🔴 **Critical** (<100kg): 42 dealer-fertilizer pairs (action required TODAY)
  - 🟡 **Warning** (<300kg): 128 pairs (monitor closely)
  - 🟠 **Caution** (<500kg): 230 pairs (restock soon)
- **Treemap**: Visual hierarchy of alerts (size = stock shortage)
  - Instantly see which district/dealer is in worst shape
- **Sortable table**: All alerts, ranked by severity

### Who Uses It
- **Emergency response** — "What's on fire right now?"
- **Regional managers** — "Which blocks need immediate attention?"
- **Procurement** — "Who's running out? Send supplies fast."

### Key Questions Answered
- "How many dealers have <100kg of any fertilizer?" (Critical = crisis)
- "Which district has the most alerts?"
- "Should dealer #999210 be a priority?"
- "Can we meet all emergency requests with current stock?"

### Action Triggers
- 🔴 >50 critical: Activate emergency supply chain
- 🟡 Spike in warnings: Pre-order stock, plan shipments
- 📍 Same district always critical: Structural problem, need permanent solution
- ✓ Mostly caution/green: System is healthy

---

## 🧠 **Intelligence** — Strategic Decisions

### What It Shows (3 Tabs)

#### Tab 1: Stock Concentration
- **Question**: "How dependent are we on a few big dealers?"
- **Visualization**: Pie charts per (district, fertilizer)
  - "In Thanjavur, the top 5 dealers hold 85% of Urea" (🔴 risky!)
- **Color coding**: Red (>80%) = monopoly risk, Yellow (60-80%) = watch, Green (<60%) = diversified
- **Use case**: Identify single points of failure

#### Tab 2: Coverage Gaps
- **Question**: "Which blocks have NO stock of certain fertilizers?"
- **Visualization**: Expandable list per fertilizer
  - "DAP is missing from 8 blocks across 3 districts"
- **Use case**: Identify supply deserts that need emergency action

#### Tab 3: Stock Volatility
- **Question**: "Which dealers are unreliable? (stock swings wildly)"
- **Metric**: Coefficient of Variation (σ/μ × 100)
  - <20% = stable, >50% = volatile, >100% = chaotic
- **Visualization**: Bar chart of top 20 most volatile dealers
  - Hover shows mean, std dev, data points
- **Use case**: Identify suppliers to diversify away from

### Who Uses It
- **Supply chain strategists** — "How resilient is our system?"
- **Risk managers** — "What could go wrong?"
- **Government planners** — "Where should we invest in infrastructure?"

### Key Questions Answered
- **Concentration**: "If dealer #364468 stops supplying, how many districts lose Urea?"
- **Gaps**: "Which regions are consistently under-served?"
- **Volatility**: "Can we predict when dealer #999210 will run out?"

### Action Triggers
- 🔴 **Concentration >80%**: Build alternative sources immediately
- 🕳️ **Same gaps every week**: Build new warehouse / license new dealer in that block
- 📈 **High volatility**: Don't rely on this dealer, use only as backup
- ✓ **Diversified + stable + no gaps**: Supply chain is resilient

---

## 🎯 **Decision Matrix**

| Decision | Go To Page | Look For |
|----------|-----------|----------|
| "Is there a crisis?" | Overview | Red color, negative delta |
| "Where are supply gaps?" | Supply Matrix | Zero-stock table, red rows |
| "What's the trend?" | Trends | Upward/downward trajectory |
| "Which products need attention?" | Deep-Dive | Donut chart imbalance |
| "Can I trust this dealer?" | Dealer Intel | Stock history pattern |
| "What are the urgent issues?" | Alerts | Critical (red) cards |
| "What could break the system?" | Intelligence | Concentration >80%, gaps, volatility |

---

## 📱 **Typical Workflow**

**Morning (5 min)**
1. Open Overview → Check KPIs and day-over-day delta
2. Check Alerts → Any critical (🔴) situations?
3. If crisis: Skip to Alerts + Intelligence for root cause

**Weekly (15 min)**
1. Trends → Review velocity (are we in surplus or deficit?)
2. Supply Matrix → Any new zero-stock regions?
3. Dealer Intel → Any dealers stopped restocking?

**Monthly (30 min)**
1. Intelligence → Full strategic review
   - Concentration risk
   - Persistent gaps
   - Volatile suppliers
2. Deep-Dive → Product/dealer health check
3. Plan adjustments for next month

**Emergency**
1. Alerts → Find all critical (🔴) pairs
2. Treemap → See which district is worst
3. Dealer Intel → Check if dealer is temporarily out or structurally broken
4. Supply Matrix → Identify alternate sources nearby
5. Deep-Dive → See who has spare inventory
6. Coordinate emergency shipment

---

**Last Updated**: 2026-03-28
**Dashboard Version**: 7 pages with Plotly
