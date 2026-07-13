"""
KPI ENGINE — Amazon Prime Day Campaign Analysis (4-6 July 2026)
Senior Data Analytics Engineer build.

Inputs
  1. Prime_Day_Campaign_Performance_4-6_July_2026.csv  (ad data, campaign-day grain)
  2. SalesDashboard-12-07-26.csv                        (store-level total sales, context)

Outputs  ->  ./output/
  1. campaign_clean.csv     cleaned, typed, row-level (Date x Campaign) with derived row KPIs
  2. campaign_agg.csv       one row per campaign, full KPIs + share/contribution metrics + rankings
  3. kpi_primary.csv        portfolio primary KPIs (long format label,value)
  4. kpi_secondary.csv      secondary KPIs (best/worst campaign per metric)
  5. store_sales_context.csv  store-level totals from the Sales Dashboard + TACOS
"""
import pandas as pd, numpy as np, os, re

BASE = "."
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------
# 1. LOAD + CLEAN CAMPAIGN FILE
# ----------------------------------------------------------------------------
CF = "Prime_Day_Campaign_Performance_4-6_July_2026.csv"
raw = pd.read_csv(CF, dtype=str, keep_default_na=False, encoding="utf-8-sig")

def to_num(series, pct=False):
    s = (series.astype(str)
               .str.replace('%', '', regex=False)
               .str.replace(',', '', regex=False)
               .str.replace('₹', '', regex=False)
               .str.strip())
    s = s.replace('', np.nan)
    out = pd.to_numeric(s, errors='coerce')
    return out

df = pd.DataFrame()
# Date -> real date
df['date'] = pd.to_datetime(raw['Date'], format='%b %d, %Y', errors='coerce').dt.date
# Campaign ID -> strip Excel ="..." injection guard
df['campaign_id'] = raw['Campaign ID'].str.replace(r'^="?|"?$', '', regex=True).str.strip()
df['campaign_name'] = raw['Campaign name'].str.strip()
df['budget_type'] = raw['Campaign budget type'].str.strip()
df['budget_amount'] = to_num(raw['Campaign budget amount'])
df['delivery_status'] = raw['Campaign delivery status'].str.strip()
df['portfolio_name'] = raw['Portfolio name'].str.strip()
df['portfolio_id'] = raw['Portfolio ID'].str.strip()
df['currency'] = raw['Budget currency'].str.strip()

# Core raw metrics
df['impressions'] = to_num(raw['Impressions']).fillna(0).astype(int)
df['clicks'] = to_num(raw['Clicks']).fillna(0).astype(int)
df['units_sold'] = to_num(raw['Units sold']).fillna(0).astype(int)
df['sales'] = to_num(raw['Sales']).fillna(0.0)
# Purchases (orders) — only "Purchases from clicks" exists in the file
df['purchases'] = to_num(raw['Purchases from clicks']).fillna(0).astype(int)

# Provided (source) rate columns — kept for validation only
src_ctr = to_num(raw['CTR'])
src_cpc = to_num(raw['CPC'])
src_roas = to_num(raw['ROAS'])
src_rpm = to_num(raw['Return per thousand impressions'])

# New-to-brand (mostly blank -> 0; kept as supplementary)
df['ntb_purchases'] = to_num(raw['Purchases (new to brand)']).fillna(0).astype(int)
df['ntb_sales'] = to_num(raw['Sales (new to brand)']).fillna(0.0)
df['ntb_units'] = to_num(raw['Units sold (new to brand)']).fillna(0).astype(int)

# ----------------------------------------------------------------------------
# 2. DERIVE SPEND + ROW-LEVEL KPIs (safe division: undefined -> NaN, not inf)
# ----------------------------------------------------------------------------
def sdiv(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    return np.where(b > 0, a / np.where(b == 0, np.nan, b), np.nan)

# Spend is NOT in the source. Derive from CPC * Clicks (0 clicks -> 0 spend).
df['spend'] = (src_cpc.fillna(0) * df['clicks']).round(2)

df['ctr']  = (sdiv(df['clicks'], df['impressions']) * 100).round(4)          # %
df['cpc']  = sdiv(df['spend'], df['clicks']).round(2)                        # currency
df['cpm']  = (sdiv(df['spend'], df['impressions']) * 1000).round(2)          # cost / 1000 impr
df['roas'] = sdiv(df['sales'], df['spend']).round(4)                         # x
df['acos'] = (sdiv(df['spend'], df['sales']) * 100).round(4)                 # %
df['conversion_rate'] = (sdiv(df['purchases'], df['clicks']) * 100).round(4) # % (orders/clicks)
df['aov']  = sdiv(df['sales'], df['purchases']).round(2)                     # currency / order
df['rpc']  = sdiv(df['sales'], df['clicks']).round(2)                        # revenue / click
df['rpi']  = sdiv(df['sales'], df['impressions']).round(6)                   # revenue / impression
df['cpp']  = sdiv(df['spend'], df['purchases']).round(2)                     # cost / purchase
df['budget_utilization'] = (sdiv(df['spend'], df['budget_amount']) * 100).round(2)  # % of daily budget

col_order = ['date','campaign_id','campaign_name','portfolio_name','portfolio_id',
             'delivery_status','budget_type','budget_amount','currency',
             'impressions','clicks','ctr','spend','cpc','cpm',
             'purchases','units_sold','sales','roas','acos','conversion_rate',
             'aov','rpc','rpi','cpp','budget_utilization',
             'ntb_purchases','ntb_sales','ntb_units']
df = df[col_order]
df.to_csv(os.path.join(OUT, "campaign_clean.csv"), index=False)

# ----------------------------------------------------------------------------
# 3. CAMPAIGN-LEVEL AGGREGATION (sum additives, then recompute rate KPIs)
# ----------------------------------------------------------------------------
g = df.groupby('campaign_id', as_index=False).agg(
    campaign_name=('campaign_name','first'),
    portfolio_name=('portfolio_name','first'),
    active_days=('date','nunique'),
    last_status=('delivery_status','last'),
    total_daily_budget=('budget_amount','sum'),   # sum of daily budgets across active days
    impressions=('impressions','sum'),
    clicks=('clicks','sum'),
    spend=('spend','sum'),
    purchases=('purchases','sum'),
    units_sold=('units_sold','sum'),
    sales=('sales','sum'),
)

g['ctr']  = (sdiv(g['clicks'], g['impressions']) * 100).round(4)
g['cpc']  = sdiv(g['spend'], g['clicks']).round(2)
g['cpm']  = (sdiv(g['spend'], g['impressions']) * 1000).round(2)
g['roas'] = sdiv(g['sales'], g['spend']).round(4)
g['acos'] = (sdiv(g['spend'], g['sales']) * 100).round(4)
g['conversion_rate'] = (sdiv(g['purchases'], g['clicks']) * 100).round(4)
g['aov']  = sdiv(g['sales'], g['purchases']).round(2)
g['rpc']  = sdiv(g['sales'], g['clicks']).round(2)
g['rpi']  = sdiv(g['sales'], g['impressions']).round(6)
g['cpp']  = sdiv(g['spend'], g['purchases']).round(2)
g['budget_utilization'] = (sdiv(g['spend'], g['total_daily_budget']) * 100).round(2)

# --- Share / contribution metrics ---
T_spend = g['spend'].sum()
T_sales = g['sales'].sum()
T_impr  = g['impressions'].sum()
g['contribution'] = (g['sales'] - g['spend'])          # net ad contribution (₹)
T_contrib = g['contribution'].sum()

g['spend_pct']      = (g['spend'] / T_spend * 100).round(2)          # share of ad spend
g['sales_pct']      = (g['sales'] / T_sales * 100).round(2)          # share of ad sales
g['revenue_share']  = g['sales_pct']                                 # alias: share of ad revenue
g['campaign_share'] = (g['impressions'] / T_impr * 100).round(2)     # share of voice (impressions)
g['contribution_pct'] = np.where(T_contrib != 0, (g['contribution'] / T_contrib * 100).round(2), np.nan)  # share of net contribution

# --- Rankings ---
g['rank_by_sales'] = g['sales'].rank(ascending=False, method='min').astype(int)
g['rank_by_spend'] = g['spend'].rank(ascending=False, method='min').astype(int)
g = g.sort_values('sales', ascending=False).reset_index(drop=True)

agg_cols = ['campaign_id','campaign_name','portfolio_name','last_status','active_days',
            'total_daily_budget','impressions','clicks','ctr','spend','cpc','cpm',
            'purchases','units_sold','sales','roas','acos','conversion_rate',
            'aov','rpc','rpi','cpp','budget_utilization','contribution',
            'spend_pct','sales_pct','revenue_share','campaign_share','contribution_pct',
            'rank_by_sales','rank_by_spend']
g[agg_cols].to_csv(os.path.join(OUT, "campaign_agg.csv"), index=False)

# ----------------------------------------------------------------------------
# 4. PRIMARY KPIs (portfolio blended)
# ----------------------------------------------------------------------------
tot_impr = int(df['impressions'].sum())
tot_clk  = int(df['clicks'].sum())
tot_spend = round(df['spend'].sum(), 2)
tot_sales = round(df['sales'].sum(), 2)
tot_purch = int(df['purchases'].sum())
tot_units = int(df['units_sold'].sum())
n_camp    = df['campaign_id'].nunique()
tot_budget = round(df['budget_amount'].sum(), 2)  # sum of daily budgets across campaign-days

def r(x, d=2):
    return None if (x is None or (isinstance(x,float) and (np.isnan(x)))) else round(x, d)

primary = [
    ("Total Sales (ad-attributed, INR)", r(tot_sales)),
    ("Total Spend (derived CPC×Clicks, INR)", r(tot_spend)),
    ("Total Purchases (orders)", tot_purch),
    ("Total Units Sold", tot_units),
    ("Total Clicks", tot_clk),
    ("Total Impressions", tot_impr),
    ("Total Campaigns (distinct)", n_camp),
    ("Average CPC (blended, INR)", r(tot_spend / tot_clk if tot_clk else np.nan)),
    ("Average CTR (blended, %)", r(tot_clk / tot_impr * 100 if tot_impr else np.nan, 4)),
    ("Average CPM (blended, INR)", r(tot_spend / tot_impr * 1000 if tot_impr else np.nan)),
    ("Average ROAS (blended, x)", r(tot_sales / tot_spend if tot_spend else np.nan, 4)),
    ("ACOS (blended, %)", r(tot_spend / tot_sales * 100 if tot_sales else np.nan, 4)),
    ("Conversion Rate (orders/clicks, %)", r(tot_purch / tot_clk * 100 if tot_clk else np.nan, 4)),
    ("Average Order Value (INR)", r(tot_sales / tot_purch if tot_purch else np.nan)),
    ("Revenue Per Click (INR)", r(tot_sales / tot_clk if tot_clk else np.nan)),
    ("Revenue Per Impression (INR)", r(tot_sales / tot_impr if tot_impr else np.nan, 6)),
    ("Cost Per Purchase (INR)", r(tot_spend / tot_purch if tot_purch else np.nan)),
    ("Budget Utilization (Spend/ΣDailyBudget, %)", r(tot_spend / tot_budget * 100 if tot_budget else np.nan)),
]
pk = pd.DataFrame(primary, columns=['kpi','value'])
pk.to_csv(os.path.join(OUT, "kpi_primary.csv"), index=False)

# ----------------------------------------------------------------------------
# 5. SECONDARY KPIs (best/worst campaign per metric) — filtered for validity
# ----------------------------------------------------------------------------
spenders = g[g['spend'] > 0]
sellers  = g[g['sales'] > 0]
clickers = g[g['clicks'] > 0]

def pick(frame, col, how):
    if frame.empty: return (None, None, None)
    row = frame.loc[frame[col].idxmax()] if how == 'max' else frame.loc[frame[col].idxmin()]
    return (row['campaign_name'], row['campaign_id'], row[col])

sec_rows = []
def add(label, frame, col, how, fmt=2):
    name, cid, val = pick(frame, col, how)
    sec_rows.append((label, name, cid, r(val, fmt) if isinstance(val,(int,float,np.floating)) else val))

add("Highest Sales Campaign", g, 'sales', 'max')
add("Highest ROAS Campaign", spenders, 'roas', 'max', 4)
add("Lowest ROAS Campaign", spenders, 'roas', 'min', 4)
add("Highest Spend Campaign", g, 'spend', 'max')
add("Best Conversion Campaign (CVR)", clickers, 'conversion_rate', 'max', 4)
add("Highest ACOS Campaign", sellers, 'acos', 'max', 4)
add("Lowest ACOS Campaign", sellers, 'acos', 'min', 4)
add("Highest CPC Campaign", clickers, 'cpc', 'max')
add("Lowest CPC Campaign", clickers, 'cpc', 'min')
sk = pd.DataFrame(sec_rows, columns=['kpi','campaign_name','campaign_id','value'])
sk.to_csv(os.path.join(OUT, "kpi_secondary.csv"), index=False)

# ----------------------------------------------------------------------------
# 6. STORE SALES CONTEXT (from Sales Dashboard snapshot) + TACOS
# ----------------------------------------------------------------------------
store_total_sales = 322815.44
store_units = 581
store_order_items = 564
store_aov = round(store_total_sales / store_order_items, 2)
tacos = round(tot_spend / store_total_sales * 100, 2)
ad_sales_share = round(tot_sales / store_total_sales * 100, 2)
ctx = pd.DataFrame([
    ("Store Ordered Product Sales (total, INR)", store_total_sales),
    ("Store Units Ordered", store_units),
    ("Store Total Order Items", store_order_items),
    ("Store Average Sales / Order Item (INR)", store_aov),
    ("Ad Sales (from campaigns, INR)", tot_sales),
    ("Ad Sales as % of Total Store Sales", ad_sales_share),
    ("TACOS (Ad Spend / Total Store Sales, %)", tacos),
], columns=['metric','value'])
ctx.to_csv(os.path.join(OUT, "store_sales_context.csv"), index=False)

# ----------------------------------------------------------------------------
# CONSOLE REPORT
# ----------------------------------------------------------------------------
print("="*70)
print("KPI ENGINE — OUTPUTS WRITTEN TO ./output/")
print("="*70)
print("\n--- PRIMARY KPIs ---")
for k,v in primary: print(f"  {k:<45} {v}")
print("\n--- SECONDARY KPIs ---")
for lbl,name,cid,val in sec_rows:
    nm = (name[:42]+'…') if name and len(name)>43 else name
    print(f"  {lbl:<34} {val:<12} {nm}")
print("\n--- STORE CONTEXT / TACOS ---")
for _,row in ctx.iterrows(): print(f"  {row['metric']:<45} {row['value']}")
print("\nRow-level rows:", len(df), "| Campaigns:", len(g))
print("Files:", os.listdir(OUT))
