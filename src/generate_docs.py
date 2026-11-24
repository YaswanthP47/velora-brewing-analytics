"""
generate_docs.py  -  STEP 4b: Create the project documentation automatically.

Run from the project folder:
        python src/generate_docs.py

It writes three Markdown files into docs/ (GitHub shows them nicely):
    docs/data_dictionary.md   every table and column: type, meaning, missing %, values/range
    docs/kpi_definitions.md   every KPI: formula, SQL, and its CURRENT value in your data
    docs/data_model.md        diagram of how tables connect + assumptions + known issues

The numbers are calculated from the real data every time you run it, so the
documentation can never be out of date.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from load_data import load_data_tables  # noqa: E402

DOCS = Path("docs")

# ------------------------------------------------------------------ descriptions
TABLE_INFO = {
    "Product_Master": ("The 13 beers Velora sells: style, ABV, costs, prices and target yield.", "product_id"),
    "Raw_Materials": ("Ingredients and packaging materials bought from suppliers.", "material_id"),
    "Suppliers": ("The 20 suppliers of raw materials.", "supplier_id"),
    "Employees": ("Staff list (synthetic aliases, no real people).", "employee_id"),
    "Distributors": ("Companies that distribute Velora beer to customers.", "distributor_id"),
    "Customers": ("Customer accounts (bars, hotels, shops...).", "customer_id"),
    "Marketing_Campaigns": ("Marketing campaigns with spend, impressions and clicks.", "campaign_id"),
    "Production_Batches": ("One row per brewing batch: planned vs actual volume, yield, status.", "batch_id"),
    "Quality_Control": ("One quality test per batch (temperature, pH, gravity, ABV, defects).", "qc_test_id"),
    "Procurement_Orders": ("Purchase orders to suppliers with expected and actual delivery dates.", "po_id"),
    "Sales_Orders": ("Order headers: who ordered, when, through which channel, and the status.", "order_id"),
    "Sales_Order_Lines": ("Order details: one row per product in an order, with sales and profit.", "order_line_id"),
    "Inventory_Movements": ("Stock changes (production in, sales out...) by product and warehouse.", "movement_id"),
    "Monthly_Expenses": ("Monthly operating expenses by category and cost centre.", "expense_id"),
    "Customer_Feedback": ("Customer reviews, complaints and return requests with text.", "feedback_id"),
    "Equipment_Maintenance": ("Maintenance jobs on brewery equipment, with downtime and cost.", "maintenance_id"),
    "Demand_History": ("Monthly units sold per product with promotion and season.", "month + product_id"),
}

D = {  # column descriptions, grouped by table
    "Product_Master": {
        "product_id": "Unique product code (VLR001...)", "product_name": "Beer name",
        "beer_style": "Style of beer", "abv_percent": "Alcohol by volume, %",
        "unit_variable_cost_eur": "Variable production cost per unit (EUR)",
        "wholesale_price_eur": "Standard price to distributors per unit (EUR)",
        "suggested_retail_price_eur": "Recommended shelf price per unit (EUR)",
        "target_yield_rate": "Planned share of volume that should survive production (0-1)",
        "pack_size_litre": "Litres per unit", "pack_format": "Package type", "launch_date": "Date the product went on sale",
        "status": "Active or discontinued"},
    "Raw_Materials": {
        "material_id": "Unique material code (RM001...)", "material_name": "Material name",
        "unit": "Unit of measure (kg, litre, unit)", "category": "Material group (Malt, Hops, Packaging...)",
        "standard_unit_cost_eur": "Standard price per unit (EUR)"},
    "Suppliers": {
        "supplier_id": "Unique supplier code (SUP001...)", "supplier_name": "Supplier name",
        "country": "Supplier country", "main_category": "Main type of goods supplied",
        "average_lead_time_days": "Stated average delivery time in days",
        "on_time_delivery_rate": "STATED share of on-time deliveries (0-1); see known issues",
        "supplier_status": "Approved or Under Review"},
    "Employees": {
        "employee_id": "Unique employee code", "employee_name_alias": "Anonymised name",
        "department": "Department", "job_title": "Job title", "hire_date": "Date hired",
        "work_location": "Work site", "monthly_salary_eur": "Monthly salary (EUR)",
        "employment_status": "Active or not"},
    "Distributors": {
        "distributor_id": "Unique distributor code (DST001...)", "distributor_name_alias": "Anonymised name",
        "country": "Distributor country", "channel_type": "Type of distribution (Retail, National...)",
        "service_level_score": "Service quality score (0-1)"},
    "Customers": {
        "customer_id": "Unique customer code (CUS0001...)", "customer_alias": "Anonymised name",
        "customer_type": "Bar, Hotel, Restaurant, Retailer or Online Customer", "country": "Customer country",
        "first_order_date": "STATED first order date; unreliable, see known issues",
        "account_size": "Small, Medium or Large"},
    "Marketing_Campaigns": {
        "campaign_id": "Unique campaign code", "campaign_name_alias": "Anonymised campaign name",
        "channel": "Marketing channel", "start_date": "Campaign start date", "spend_eur": "Money spent (EUR)",
        "impressions": "Times the ad was shown", "clicks": "Times the ad was clicked",
        "featured_product_id": "Product promoted (links to Product_Master)"},
    "Production_Batches": {
        "batch_id": "Unique batch code (BAT00001...)", "production_date": "Date the batch was brewed",
        "product_id": "Beer produced (links to Product_Master)", "production_line": "Maribor Line A, B or C",
        "planned_volume_litre": "Planned litres", "actual_volume_litre": "Litres actually produced",
        "production_loss_litre": "planned - actual litres", "yield_rate": "actual / planned (0-1)",
        "estimated_batch_cost_eur": "Estimated cost of the batch (EUR)", "shift_count": "Number of shifts used (1-4)",
        "batch_status": "Completed, Delayed or On Hold"},
    "Quality_Control": {
        "qc_test_id": "Unique test code (QCT00001...)", "batch_id": "Batch tested (links to Production_Batches)",
        "test_date": "Date of the test (same as production date)", "temperature_c": "Temperature in degrees C",
        "ph_value": "Acidity (pH)", "specific_gravity": "Density of the beer relative to water",
        "measured_abv_percent": "Measured alcohol, %", "colour_ebc": "Beer colour (EBC scale)",
        "defect_units": "Number of defective units found", "quality_status": "Pass or Review"},
    "Procurement_Orders": {
        "po_id": "Unique purchase order code (PO00001...)", "order_date": "Date the order was placed",
        "supplier_id": "Supplier (links to Suppliers)", "material_id": "Material (links to Raw_Materials)",
        "quantity_ordered": "Quantity ordered (in the material's unit)", "unit_cost_eur": "Price paid per unit (EUR)",
        "purchase_value_eur": "quantity x unit cost (EUR)", "expected_delivery_date": "Promised delivery date",
        "actual_delivery_date": "Date it actually arrived", "lead_time_days": "actual delivery - order date, in days",
        "po_status": "Received or Partially Received"},
    "Sales_Orders": {
        "order_id": "Unique order code (ORD000001...)", "order_date": "Date of the order",
        "customer_id": "Customer (links to Customers)", "distributor_id": "Distributor (links to Distributors)",
        "sales_channel": "Distributor, Online, Hospitality or Retail", "ship_to_country": "Delivery country",
        "order_status": "Delivered, Shipped, Open or Cancelled", "currency": "Always EUR"},
    "Sales_Order_Lines": {
        "order_line_id": "Unique line code (order id + line number)", "order_id": "Order (links to Sales_Orders)",
        "product_id": "Product sold (links to Product_Master)", "quantity_units": "Units sold",
        "unit_selling_price_eur": "Price per unit before discount (rounded to 2 decimals)",
        "discount_rate": "Discount given (0-1)", "net_sales_eur": "Sales after discount (EUR)",
        "estimated_cogs_eur": "Estimated cost of goods sold (EUR)", "gross_profit_eur": "net sales - COGS (EUR)"},
    "Inventory_Movements": {
        "movement_id": "Unique movement code", "movement_date": "Date of the stock change",
        "product_id": "Product (links to Product_Master)", "warehouse": "Warehouse name",
        "movement_type": "Kind of movement (production receipt, sales dispatch...)",
        "quantity_change_units": "Units added (+) or removed (-)",
        "batch_reference": "Batch that caused it, if any (empty otherwise)",
        "order_reference": "Order that caused it, if any (empty otherwise)"},
    "Monthly_Expenses": {
        "expense_id": "Unique expense code", "expense_month": "Month of the expense",
        "expense_category": "Type of cost", "amount_eur": "Amount (EUR)", "cost_centre": "Department charged"},
    "Customer_Feedback": {
        "feedback_id": "Unique feedback code (FB00001...)", "feedback_date": "Date received",
        "customer_id": "Customer (links to Customers)", "product_id": "Product (links to Product_Master)",
        "feedback_type": "Complaint, Return Request or Review", "feedback_text": "The customer's comment (12 distinct sentences)",
        "sentiment_label": "Positive, Neutral or Negative", "case_status": "Resolved, Open or Escalated",
        "issue_category": "Packaging, Delivery, Order Accuracy, Product Quality or Customer Service; unreliable, see known issues"},
    "Equipment_Maintenance": {
        "maintenance_id": "Unique job code", "maintenance_date": "Date of the job", "equipment": "Machine serviced",
        "maintenance_type": "Preventive or corrective", "downtime_hours": "Hours the machine was stopped",
        "maintenance_cost_eur": "Cost of the job (EUR)", "maintenance_status": "Status of the job"},
    "Demand_History": {
        "month": "Month (first day)", "product_id": "Product (links to Product_Master)",
        "units_sold": "Units sold in that month", "promotion_discount_rate": "Promotion discount that month (0-1)",
        "season": "Season label; inconsistent, see known issues"},
}


def md_escape(x):
    return str(x).replace("|", "\\|")


def describe_values(s):
    """Short text: range for numbers and dates, value list for categories."""
    s = s.dropna()
    if s.empty:
        return "empty"
    if pd.api.types.is_datetime64_any_dtype(s):
        return f"{s.min():%Y-%m-%d} to {s.max():%Y-%m-%d}"
    if pd.api.types.is_numeric_dtype(s):
        return f"{s.min():g} to {s.max():g}"
    n = s.nunique()
    if n == len(s):
        return "unique IDs / values"
    if n <= 8:
        return ", ".join(map(str, sorted(s.unique())))
    return f"{n} distinct values"


def type_name(s):
    if pd.api.types.is_datetime64_any_dtype(s):
        return "date"
    if pd.api.types.is_integer_dtype(s):
        return "integer"
    if pd.api.types.is_float_dtype(s):
        return "decimal"
    return "text"


# ------------------------------------------------------------------ data dictionary
def write_data_dictionary(t):
    out = ["# Data Dictionary", "",
           "_Generated automatically by `python src/generate_docs.py` from the Excel file._", "",
           f"{len(t)} tables, {sum(len(d) for d in t.values()):,} rows in total. "
           "All data is **synthetic** (no real people or companies).", "", "## Tables at a glance", "",
           "| Table | Rows | Columns | Primary key | What it holds |", "|---|---:|---:|---|---|"]
    for n, df in t.items():
        purpose, pk = TABLE_INFO[n]
        out.append(f"| [{n}](#{n.lower()}) | {len(df):,} | {df.shape[1]} | `{pk}` | {purpose} |")
    missing = []
    for n, df in t.items():
        out += ["", f"## {n}", "", TABLE_INFO[n][0], "",
                f"Rows: **{len(df):,}** | Primary key: `{TABLE_INFO[n][1]}`", "",
                "| Column | Type | Meaning | Missing | Values / range |", "|---|---|---|---:|---|"]
        for c in df.columns:
            desc = D[n].get(c)
            if desc is None:
                missing.append(f"{n}.{c}")
                desc = "(no description yet)"
            out.append(f"| `{c}` | {type_name(df[c])} | {md_escape(desc)} | {df[c].isna().mean():.0%} | "
                       f"{md_escape(describe_values(df[c]))} |")
    (DOCS / "data_dictionary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    return missing


# ------------------------------------------------------------------ KPI definitions
def compute_kpis(t):
    pb, qc, po = t["Production_Batches"], t["Quality_Control"], t["Procurement_Orders"]
    so, sl, mc = t["Sales_Orders"], t["Sales_Order_Lines"], t["Marketing_Campaigns"]
    fb, inv = t["Customer_Feedback"], t["Inventory_Movements"]
    ok_lines = sl.merge(so[["order_id", "order_status"]], on="order_id")
    ok_lines = ok_lines[ok_lines.order_status != "Cancelled"]
    late = pd.to_datetime(po.actual_delivery_date) > pd.to_datetime(po.expected_delivery_date)
    non_cancelled = (so.order_status != "Cancelled").sum()
    complaints = (fb.feedback_type == "Complaint").sum()
    stock = inv.groupby("product_id").quantity_change_units.sum()
    return {
        "yield": 100 * pb.yield_rate.mean(), "loss": pb.production_loss_litre.sum(),
        "ontime": 100 * (1 - late.mean()), "stated_ontime": 100 * t["Suppliers"].on_time_delivery_rate.mean(),
        "gp": ok_lines.gross_profit_eur.sum(), "sales": ok_lines.net_sales_eur.sum(),
        "gm": 100 * ok_lines.gross_profit_eur.sum() / ok_lines.net_sales_eur.sum(),
        "ctr": 100 * mc.clicks.sum() / mc.impressions.sum(),
        "review": 100 * (qc.quality_status == "Review").mean(), "n_review": int((qc.quality_status == "Review").sum()),
        "n_qc": len(qc), "complaints": int(complaints), "non_cancelled": int(non_cancelled),
        "complaint_rate": 100 * complaints / non_cancelled, "neg_stock": int((stock < 0).sum()), "n_prod": len(stock),
    }


def write_kpis(t):
    k = compute_kpis(t)
    out = [
        "# KPI Definitions", "",
        "_Formulas come from the `KPI_Glossary` sheet; values are calculated from your data by "
        "`python src/generate_docs.py`._", "",
        "| KPI | Formula | Current value | Better is | Notes |", "|---|---|---:|---|---|",
        f"| Production yield | `actual_volume_litre / planned_volume_litre` | **{k['yield']:.1f}%** (average of batches) | Higher | Per batch; target per product is in Product_Master |",
        f"| Production loss | `planned_volume_litre - actual_volume_litre` | **{k['loss']:,.0f} litres** (total) | Lower | |",
        f"| Supplier on-time rate | `on-time deliveries / total deliveries` | **{k['ontime']:.1f}%** | Higher | On time = actual delivery <= expected delivery. The Suppliers sheet states {k['stated_ontime']:.0f}%, which conflicts; use the calculated value |",
        f"| Gross profit | `net_sales_eur - estimated_cogs_eur` | **EUR {k['gp']:,.0f}** | Higher | Cancelled orders excluded |",
        f"| Gross margin % | `gross_profit_eur / net_sales_eur` | **{k['gm']:.1f}%** | Higher | On net sales of EUR {k['sales']:,.0f}, cancelled orders excluded |",
        f"| Campaign CTR | `clicks / impressions` | **{k['ctr']:.2f}%** (all campaigns) | Interpret by channel | Compare within one channel only |",
        f"| Batch quality review rate | `Review batches / all batches` | **{k['review']:.1f}%** ({k['n_review']} of {k['n_qc']}) | Lower | |",
        f"| Customer complaint rate | `complaints / non-cancelled orders` | **{k['complaint_rate']:.1f}%** ({k['complaints']} of {k['non_cancelled']:,}) | Lower | Denominator chosen by us: non-cancelled orders. Complaints = feedback_type 'Complaint' |",
        "| Demand forecast error | `MAE or RMSE between forecast and actual` | _computed in Step 8_ | Lower | Demand_History holds only actual `units_sold`, no forecast column, so the forecast must come from our own model |",
        f"| Inventory movement | `sum(quantity_change_units) by product and warehouse` | {k['neg_stock']} of {k['n_prod']} products below zero | n/a | There is no opening stock, so totals are net movements, not stock on hand |",
        "", "## SQL versions (run against `data/velora.db`)", "",
        "```sql", "-- Production yield (average of batches) and total loss",
        "SELECT ROUND(100*AVG(yield_rate),1) AS yield_pct, SUM(production_loss_litre) AS loss_litre",
        "FROM Production_Batches;", "",
        "-- Supplier on-time rate",
        "SELECT ROUND(100.0*SUM(actual_delivery_date <= expected_delivery_date)/COUNT(*),1) AS on_time_pct",
        "FROM Procurement_Orders;", "",
        "-- Gross margin % (cancelled orders excluded)",
        "SELECT ROUND(100.0*SUM(l.gross_profit_eur)/SUM(l.net_sales_eur),1) AS gross_margin_pct",
        "FROM Sales_Order_Lines l JOIN Sales_Orders o ON o.order_id = l.order_id",
        "WHERE o.order_status <> 'Cancelled';", "",
        "-- Batch quality review rate",
        "SELECT ROUND(100.0*SUM(quality_status='Review')/COUNT(*),1) AS review_rate_pct FROM Quality_Control;",
        "```", "",
        "## Pandas versions", "", "```python",
        "yield_pct   = production_batches['yield_rate'].mean() * 100",
        "on_time_pct = (po['actual_delivery_date'] <= po['expected_delivery_date']).mean() * 100",
        "gross_margin = lines['gross_profit_eur'].sum() / lines['net_sales_eur'].sum() * 100",
        "review_rate = (qc['quality_status'] == 'Review').mean() * 100",
        "```",
    ]
    (DOCS / "kpi_definitions.md").write_text("\n".join(out) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ data model + assumptions
DATA_MODEL = """# Data Model, Assumptions and Known Issues

## 1. How the tables connect

```mermaid
erDiagram
    Product_Master ||--o{ Sales_Order_Lines : "product_id"
    Product_Master ||--o{ Production_Batches : "product_id"
    Product_Master ||--o{ Inventory_Movements : "product_id"
    Product_Master ||--o{ Customer_Feedback : "product_id"
    Product_Master ||--o{ Demand_History : "product_id"
    Product_Master ||--o{ Marketing_Campaigns : "featured_product_id"
    Customers ||--o{ Sales_Orders : "customer_id"
    Customers ||--o{ Customer_Feedback : "customer_id"
    Distributors ||--o{ Sales_Orders : "distributor_id"
    Sales_Orders ||--|{ Sales_Order_Lines : "order_id"
    Production_Batches ||--o| Quality_Control : "batch_id"
    Production_Batches ||--o{ Inventory_Movements : "batch_reference"
    Sales_Orders ||--o{ Inventory_Movements : "order_reference"
    Suppliers ||--o{ Procurement_Orders : "supplier_id"
    Raw_Materials ||--o{ Procurement_Orders : "material_id"
```

Standalone tables with no links: `Employees`, `Monthly_Expenses`, `Equipment_Maintenance`.
All links were checked in Step 2 (no orphan IDs).

**Business flow:** raw materials are bought from suppliers (`Procurement_Orders`), brewed into
beer (`Production_Batches`), tested (`Quality_Control`), moved through stock (`Inventory_Movements`),
sold to customers (`Sales_Orders` + `Sales_Order_Lines`), and customers react (`Customer_Feedback`).

## 2. Dataset assumptions (original file)

- Fictional Slovenian brewery with 13 beers. All data is synthetic education data, not real records.
- Data period is 2023-01-01 to 2026-10-31 for transactions. `Demand_History` runs to 2026-12 (forecast-period months).
- Currency is EUR. The INR 700 crore valuation is a teaching scenario, not a market value.
- Cancelled orders keep their order lines. **Revenue KPIs exclude cancelled orders.**
- `unit_selling_price_eur` is rounded to 2 decimals, so recomputed net sales differ from the stored value by up to 0.5%. We allow a 1% tolerance.
- Production batches occur exactly every 3 days; each has exactly one QC test on the same day.
- `batch_status`, `quality_status` and `order_status` appear to be assigned independently of the measurements
  and dates in the file. Do not expect strong predictive signal in Step 7 for these targets.
- This is an analytical simulation only. It is not regulatory, excise or food-safety evidence.

## 3. Known data issues (found in validation)

| # | Issue | Evidence | How we handle it |
|---|---|---|---|
| 1 | Supplier on-time rate conflicts | Suppliers sheet says about 90%; Procurement_Orders gives about 43% | Use the calculated value (KPI_Glossary formula) |
| 2 | `first_order_date` unreliable | About 52% of orders happen before the customer's first_order_date | Derive it from Sales_Orders |
| 3 | Supplier names do not match categories | e.g. "Alpine Hops GmbH" is listed as "Process supplies", "Maribor Labels" as "Malt" | Do not use `main_category` for analysis; use the Raw_Materials category of what was bought |
| 4 | `issue_category` is unreliable | Each feedback sentence has one sentiment, but the category is random relative to the text | For NLP, trust `sentiment_label`; check `issue_category` before using it as a target |
| 5 | `feedback_text` has only 12 distinct sentences | 500 rows, 12 texts | NLP models will score unrealistically high; say so in the report |
| 6 | Inventory has no opening stock | Movement totals are negative for products | Report net movements, never stock on hand |
| 7 | Expenses exceed gross profit every month | Synthetic cost levels | Describe as a dataset property, not a business conclusion |
| 8 | `season` in Demand_History is inconsistent | e.g. January labelled Spring; labels differ between products in the same month | Rebuild season from the month in Step 6 |
| 9 | 2026 is incomplete | Transactions stop at 2026-10-31 | Compare Jan-Oct across years. Like for like, sales are flat (EUR 1.47M to 1.50M); the full-year drop is only the missing Nov-Dec |
| 10 | Procurement spend far above revenue | Purchases EUR 28.2M vs net sales EUR 6.8M (about 4x) | Compare suppliers and categories only; never compare purchases with revenue |
| 11 | Demand_History does not reconcile with orders | Reports 54%-63% of order-line units and rises while orders are flat | Treat it as a separate series when forecasting |
| 12 | `customer_type` and `sales_channel` unrelated | An "Online Customer" buys only 2% through the Online channel, like every other type | Do not use customer_type to explain channel behaviour |
| 13 | Online orders are tiny | Online has 26% of orders but 2.2% of sales (average 40 units per line, maximum 80) | Analyse Online separately from other channels |

## 4. Synthetic data generator (`src/generate_synthetic_data.py`)

Creates new data with the same columns as the original. Same `--seed` gives identical files.
Use `--scale 0.5` for half the rows.

| Area | Main assumption |
|---|---|
| Suppliers | 20 suppliers; name, country and category consistent; lead time 2-18 days; stated on-time rate 82%-97% |
| Procurement | 1,200 orders; supplier delivers only its own material category; late with probability (1 - stated on-time rate); lateness 1-11 days |
| Production | Batch every few days; planned 700-3,187 L; yield ~ Normal(product target, 0.045) clipped 75%-99%; status 61.5% Completed / 19.6% Delayed / 18.9% On Hold |
| Quality control | One test per batch; Review rate 29.7%, independent of measurements (as in the original) |
| Sales | 4,500 orders, 1-4 lines each; only products already launched; price = wholesale x 0.94-1.08; discount 0%-18%; cancelled 17% |
| Customers | `first_order_date` derived from orders, so no order precedes it |
| Feedback | 12 sentences; each fixes sentiment AND issue category (so categories are learnable) |

**Deliberate differences from the original** (fixes for issues 1, 2, 3 and 4 above): supplier on-time rate is consistent
with deliveries, first_order_date is consistent with orders, supplier categories match names, and issue_category matches the text.

The generator checks itself (unique IDs, valid links, correct formulas, identical column names) and prints a
KPI comparison against the original file.
"""


def main():
    DOCS.mkdir(exist_ok=True)
    t = load_data_tables()
    missing = write_data_dictionary(t)
    write_kpis(t)
    (DOCS / "data_model.md").write_text(DATA_MODEL, encoding="utf-8")
    print("Written: docs/data_dictionary.md, docs/kpi_definitions.md, docs/data_model.md")
    if missing:
        print("Columns without a description:", missing)
    else:
        print("All columns have a description.")


if __name__ == "__main__":
    main()
