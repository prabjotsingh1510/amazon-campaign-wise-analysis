# Data Dictionary & Dataset Understanding

**Project:** Amazon Prime Day Campaign-wise Analysis
**Prepared by:** Senior Data Analytics Engineer / BI Architect
**Date range analysed:** 04–06 July 2026 (Prime Day)
**Currency:** INR (₹)

---

## 1. Files Overview

| File | Grain | Rows | Purpose |
|---|---|---|---|
| `Prime_Day_Campaign_Performance_4-6_July_2026.csv` | 1 row = 1 Campaign × 1 Day | 650 data rows | Sponsored-ads performance (the analytical core) |
| `SalesDashboard-12-07-26.csv` | Store-level report, multi-section | 91 lines | Total store sales (organic + ads); **context only** — does NOT join to campaigns |

> **Key structural finding:** The two files operate at different grains. The campaign file is transactional (campaign/day). The Sales Dashboard is a formatted business report (snapshot + hourly time-series + YoY table). They cannot be row-joined; the dashboard supplies **store totals for TACOS**.

---

## 2. Campaign File — Data Dictionary (24 source columns)

| # | Source Column | Detected Type | Category | Notes / Issues |
|---|---|---|---|---|
| 0 | Date | Text → Date | **Date** | Format `"Jul 06, 2026"`. Only 3 dates. Cleaned → ISO `date`. |
| 1 | Campaign ID | Text (corrupt) | Product/Key | Stored as Excel formula `="143418681856266"` (anti-truncation guard). **Cleaned** → plain digits. |
| 2 | Campaign name | Text | Product | 227 distinct. Inconsistent naming conventions (see §6). Primary business label. |
| 3 | Campaign budget type | Categorical | Budget | Single value `DAILY_BUDGET` (zero variance). |
| 4 | Campaign budget amount | Integer | **Budget** | Daily budget cap. 31 distinct values. |
| 5 | Campaign delivery status | Categorical | Campaign | `ENABLED` / `PAUSED` only. |
| 6 | Portfolio name | Categorical | Campaign | 14 distinct (`No Portfolio`, `Branded KWs`, `Brush`, …). |
| 7 | Portfolio ID | Text | Campaign | 14 distinct. `-1` = No Portfolio. Redundant with Portfolio name. |
| 8 | Budget currency | Categorical | Budget | Single value `INR` (zero variance). |
| 9 | Impressions | Integer | **Traffic** | 0 blanks. |
| 10 | Clicks | Integer | **Traffic** | 0 blanks. |
| 11 | CTR | Percent text | Traffic | `Clicks/Impr`. **Blank when Impressions = 0** (14 rows). Recomputed. |
| 12 | CPC | Decimal | **Campaign/Cost** | **Blank when Clicks = 0** (272 rows = 41.8%) — structural, not missing. |
| 13 | Units sold | Integer | **Purchase** | Attributed units. |
| 14 | Sales | Decimal | **Sales** | Ad-attributed revenue. |
| 15 | ROAS | Decimal | Campaign | `Sales/Spend`. **Blank when Spend = 0** (269 rows). Recomputed. |
| 16 | Return per thousand impressions | Decimal | Sales | `Sales/Impr×1000` (RPM revenue). Blank when Impr=0. |
| 17 | Purchases from clicks | Integer | **Purchase** | The **only** purchases/orders column → used as `purchases`. |
| 18 | Sales from clicks | Decimal | Sales | **Duplicate of `Sales`** (3 tiny mismatches / 650). |
| 19 | Units sold from clicks | Integer | Purchase | **Duplicate of `Units sold`** (3 mismatches / 650). |
| 20 | Purchases (new to brand) | Integer | Purchase | 87.1% blank. Supplementary. |
| 21 | Sales (new to brand) | Decimal | Sales | 87.1% blank. Supplementary. |
| 22 | Units sold (new to brand) | Integer | Purchase | 87.1% blank. Supplementary. |
| 23 | Percent of sales new to brand | Decimal | Sales | 95.2% blank. Supplementary. |

### ⚠️ Critical: there is **no Spend / Cost column** in the source
Spend is derived: **`Spend = CPC × Clicks`** (0 clicks ⇒ 0 spend). Validated against the alternative `Sales ÷ ROAS` — the two agree within ₹0.02 on all 144 overlapping rows. Total derived Spend = **₹67,144.07**.

---

## 3. Data-Type Summary

- **Dates:** `Date` (→ ISO date).
- **Integers:** Impressions, Clicks, Units sold, Purchases from clicks, Budget amount, NTB purchases/units.
- **Decimals/Floats:** CPC, Sales, ROAS, Return/1000-impr, Sales from clicks, NTB sales, Percent NTB.
- **Percent-as-text:** CTR (`2.4735%`) — stripped `%`, stored numeric.
- **Categorical:** Budget type, Delivery status, Portfolio name, Currency.
- **Identifiers/Text:** Campaign ID (Excel-escaped), Campaign name, Portfolio ID.

---

## 4. Missing Values (all explained — none are true data gaps)

| Column | Blank % | Reason |
|---|---|---|
| Percent of sales NTB | 95.2% | Only populated when NTB sales exist |
| NTB purchases/sales/units | 87.1% | NTB is a rare sub-segment |
| CPC | 41.8% | Structural: undefined when Clicks = 0 |
| ROAS | 41.4% | Structural: undefined when Spend = 0 |
| CTR / Return-per-1000-impr | 2.2% | Structural: undefined when Impressions = 0 |

In the clean dataset, rate KPIs remain **NaN** where mathematically undefined (never forced to 0 or ∞), so averages stay statistically honest.

---

## 5. Inconsistencies Detected & Handled

1. **Excel formula injection** in Campaign ID (`="…"`) → stripped.
2. **Zero-variance columns:** Budget type (`DAILY_BUDGET`), Currency (`INR`) — carry no analytical signal.
3. **Redundant keys:** Portfolio ID ↔ Portfolio name (1:1).
4. **Naming chaos** in Campaign name: mixed delimiters (`|`, `_`, `\`), inconsistent casing (`SPM` vs `spt comp`), stray spaces.
5. **No fully-duplicate rows; no duplicate column headers.** (Date, Campaign ID) is a unique key.
6. **Grain gotcha:** 227 campaigns × 3 days = 681 possible, but only 650 rows → not every campaign runs every day (use `active_days`).
7. **Edge KPIs:** e.g. CVR = 200% (2 orders on 1 click) is valid but extreme — surfaced, not suppressed.

---

## 6. Same Metric, Different Names (deduplicated in the engine)

| Kept (canonical) | Duplicate / alias in source | Decision |
|---|---|---|
| `sales` | `Sales from clicks` | Identical (≈); keep one |
| `units_sold` | `Units sold from clicks` | Identical (≈); keep one |
| `purchases` | `Purchases from clicks` | Only source of orders; renamed |
| `campaign_share` / `spend_pct` | "Campaign Share" vs "Spend %" | Made distinct (see §8) |
| `revenue_share` / `sales_pct` | "Revenue Share" vs "Sales %" | `revenue_share` = alias of `sales_pct` |

---

## 7. Metric Categorisation

- **Campaign metrics:** Campaign ID/name, delivery status, portfolio, ROAS, CPC, ACOS.
- **Sales metrics:** Sales, Sales from clicks, Return-per-1000-impr, NTB sales, % sales NTB.
- **Traffic metrics:** Impressions, Clicks, CTR, CPM.
- **Purchase metrics:** Purchases (orders), Units sold, CVR, AOV, NTB purchases/units.
- **Budget metrics:** Budget type, Budget amount, Currency, Budget utilization.
- **Product metrics:** Campaign name (encodes ASIN / product / match-type), Portfolio.
- **Date fields:** Date (campaign file), hourly timestamps (dashboard).

---

## 8. Derived KPI Definitions (the Engine)

**Spend = CPC × Clicks**. All rate KPIs use safe division (undefined ⇒ NaN).

| KPI | Formula |
|---|---|
| CTR | Clicks / Impressions × 100 |
| CPC | Spend / Clicks |
| CPM | Spend / Impressions × 1000 |
| ROAS | Sales / Spend |
| ACOS | Spend / Sales × 100 |
| Conversion Rate (CVR) | Purchases / Clicks × 100 |
| AOV | Sales / Purchases |
| Revenue Per Click (RPC) | Sales / Clicks |
| Revenue Per Impression (RPI) | Sales / Impressions |
| Cost Per Purchase (CPP) | Spend / Purchases |
| Budget Utilization | Spend / Σ(Daily Budget) × 100 |

**Share / contribution metrics (campaign level):**

| Metric | Definition |
|---|---|
| `spend_pct` | Campaign Spend ÷ Total Spend — share of ad investment |
| `sales_pct` | Campaign Sales ÷ Total Sales — share of ad revenue |
| `revenue_share` | Alias of `sales_pct` |
| `campaign_share` | Campaign Impressions ÷ Total Impressions — **share of voice** (kept distinct from spend) |
| `contribution` (₹) | Sales − Spend — net ad contribution |
| `contribution_pct` | Campaign contribution ÷ Total contribution — share of net profitability |

**TACOS** (uses the Sales Dashboard total): Ad Spend ÷ **Total Store Sales** × 100 = **20.8%** (vs ACOS 34.7% on ad-only sales). Ad sales = **59.9%** of total store sales.

---

## 9. Output Files (`/output`)

| File | Grain | Use |
|---|---|---|
| `campaign_clean.csv` | Campaign × Day (650) | Cleaned, typed, row-level facts + row KPIs |
| `campaign_agg.csv` | Campaign (227) | Full KPIs + shares + rankings — **primary dashboard table** |
| `kpi_primary.csv` | 1 portfolio | 18 headline KPIs |
| `kpi_secondary.csv` | 9 rows | Best/worst campaign per metric |
| `store_sales_context.csv` | 1 store | Store totals + TACOS |
