# Amazon Prime Day 2026 — Campaign-wise Analysis

End-to-end analytics for the **Prime Day 2026 (04–06 July)** Sponsored-Ads campaigns:
data understanding → cleaned analytics-ready datasets → a **KPI engine** → an intelligent,
CEO-ready **executive dashboard**.

All figures are computed dynamically from the source data — nothing is hardcoded.

## Highlights

| Metric | Value |
|---|---|
| Ad Sales (attributed) | ₹1,93,282 |
| Ad Spend (derived CPC×Clicks) | ₹67,144 |
| Blended ROAS | 2.88× |
| ACOS | 34.7% |
| Orders / Units | 380 / 389 |
| Campaigns | 227 (650 campaign-days) |
| Budget Utilization | 16.4% |
| TACOS (vs total store sales) | 20.8% |

**Key findings:** revenue is concentrated (top 5 campaigns = 26.6% of sales); 77 campaigns
spent ₹6,345 (9.5% of budget) with **zero** attributed sales; hidden gems like
`SPPT|MyFirstSwingingJungleCombo` returned **195.8× ROAS** on ₹11 of spend.

## Repository structure

```
├── Prime_Day_Campaign_Performance_4-6_July_2026.csv   # source: ad data (campaign × day)
├── SalesDashboard-12-07-26.csv                         # source: store-level total sales
├── kpi_engine.py                                       # reproducible KPI engine
└── output/
    ├── DATA_DICTIONARY.md      # full data dictionary, type/null/duplicate audit
    ├── campaign_clean.csv      # cleaned, typed, row-level facts + row KPIs (650 rows)
    ├── campaign_agg.csv        # per-campaign KPIs + share/contribution metrics + rankings (227)
    ├── kpi_primary.csv         # 18 portfolio headline KPIs
    ├── kpi_secondary.csv       # best/worst campaign per metric
    ├── store_sales_context.csv # store totals + TACOS
    ├── data.js                 # embedded dataset powering the dashboard (auto-generated)
    └── dashboard.html          # the executive dashboard (open in a browser)
```

## The dashboard

Open **`output/dashboard.html`** in any modern browser (keep `data.js` beside it).

7 sections — Executive Summary · Daily Trend · Campaign Leaderboard · Funnel · Comparison ·
Executive Insights · Opportunity Center — plus an intelligence layer: per-campaign hover
summaries, auto-narrative, smart alerts, metric explainers, a 0–100 health score,
PDF/Excel/PNG export, full filtering, dark/light mode. Everything recomputes client-side.

## Reproducing the pipeline

```bash
pip install pandas numpy
python kpi_engine.py          # regenerates everything in ./output
```

## Data notes

- **Currency:** INR. **Grain:** the campaign file is 1 row per campaign per day.
- **Spend is derived** as `CPC × Clicks` (no native spend column in the source),
  validated against `Sales ÷ ROAS`.
- Blank `CPC`/`ROAS`/`CTR` are **structural** (undefined when clicks/spend/impressions = 0),
  not missing data — kept `NaN` so averages stay honest.
- The two source files sit at different grains and are not row-joined; the Sales Dashboard
  supplies store totals for TACOS context.

See [`output/DATA_DICTIONARY.md`](output/DATA_DICTIONARY.md) for the complete field-by-field reference.
