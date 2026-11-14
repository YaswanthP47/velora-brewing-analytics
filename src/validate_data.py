"""
validate_data.py  -  STEP 2b: Check the quality of the data.

Run it from the project folder with:
        python src/validate_data.py

It runs 6 groups of checks and writes a report to reports/validation_report.txt
    1. Shape (rows x columns)
    2. Missing values
    3. Duplicate IDs
    4. Foreign keys (do linked IDs really exist?)
    5. Date ranges
    6. Calculation checks (do the numbers add up?)
"""

import sys
from pathlib import Path

import pandas as pd

# Make "from load_data import ..." work no matter where you run the script from.
sys.path.insert(0, str(Path(__file__).parent))
from load_data import load_data_tables  # noqa: E402

REPORT_FILE = Path("reports/validation_report.txt")
LINES = []  # we collect every message here, then print + save at the end


def log(text=""):
    """Print a line AND remember it for the report file."""
    print(text)
    LINES.append(text)


def section(title):
    log("\n" + "=" * 70)
    log(title)
    log("=" * 70)


# --------------------------------------------------------------------------
# CHECK 1: shape
# --------------------------------------------------------------------------
def check_shapes(t):
    section("CHECK 1: Table sizes")
    for name, df in t.items():
        log(f"{name:<22} {df.shape[0]:>6} rows x {df.shape[1]:>2} columns")


# --------------------------------------------------------------------------
# CHECK 2: missing values
# --------------------------------------------------------------------------
def check_missing(t):
    section("CHECK 2: Missing values")
    found = False
    for name, df in t.items():
        miss = df.isna().sum()
        miss = miss[miss > 0]
        for col, n in miss.items():
            found = True
            log(f"{name}.{col}: {n} missing ({n / len(df):.1%})")
    if not found:
        log("No missing values anywhere.")
    log("\nNote: Inventory_Movements batch_reference / order_reference are EXPECTED")
    log("to be empty (a sales dispatch has no batch, a production receipt has no order).")


# --------------------------------------------------------------------------
# CHECK 3: duplicate IDs
# --------------------------------------------------------------------------
PRIMARY_KEYS = {
    "Product_Master": "product_id",
    "Raw_Materials": "material_id",
    "Suppliers": "supplier_id",
    "Employees": "employee_id",
    "Distributors": "distributor_id",
    "Customers": "customer_id",
    "Marketing_Campaigns": "campaign_id",
    "Production_Batches": "batch_id",
    "Quality_Control": "qc_test_id",
    "Procurement_Orders": "po_id",
    "Sales_Orders": "order_id",
    "Sales_Order_Lines": "order_line_id",
    "Inventory_Movements": "movement_id",
    "Monthly_Expenses": "expense_id",
    "Customer_Feedback": "feedback_id",
    "Equipment_Maintenance": "maintenance_id",
}


def check_duplicates(t):
    section("CHECK 3: Duplicate IDs (each ID must be unique)")
    for name, key in PRIMARY_KEYS.items():
        dup = t[name][key].duplicated().sum()
        status = "OK  " if dup == 0 else "FAIL"
        log(f"[{status}] {name}.{key}: {dup} duplicates")
    full = {n: int(t[n].duplicated().sum()) for n in t}
    full = {n: c for n, c in full.items() if c > 0}
    log(f"\nFully duplicated rows: {full if full else 'none'}")


# --------------------------------------------------------------------------
# CHECK 4: foreign keys
# --------------------------------------------------------------------------
FOREIGN_KEYS = [
    # (child table, child column, parent table, parent column)
    ("Sales_Orders", "customer_id", "Customers", "customer_id"),
    ("Sales_Orders", "distributor_id", "Distributors", "distributor_id"),
    ("Sales_Order_Lines", "order_id", "Sales_Orders", "order_id"),
    ("Sales_Order_Lines", "product_id", "Product_Master", "product_id"),
    ("Production_Batches", "product_id", "Product_Master", "product_id"),
    ("Quality_Control", "batch_id", "Production_Batches", "batch_id"),
    ("Procurement_Orders", "supplier_id", "Suppliers", "supplier_id"),
    ("Procurement_Orders", "material_id", "Raw_Materials", "material_id"),
    ("Inventory_Movements", "product_id", "Product_Master", "product_id"),
    ("Customer_Feedback", "customer_id", "Customers", "customer_id"),
    ("Customer_Feedback", "product_id", "Product_Master", "product_id"),
    ("Marketing_Campaigns", "featured_product_id", "Product_Master", "product_id"),
    ("Demand_History", "product_id", "Product_Master", "product_id"),
]


def check_foreign_keys(t):
    section("CHECK 4: Foreign keys (does every linked ID exist in its parent table?)")
    for child, ccol, parent, pcol in FOREIGN_KEYS:
        orphans = ~t[child][ccol].isin(t[parent][pcol])
        n = int(orphans.sum())
        status = "OK  " if n == 0 else "FAIL"
        log(f"[{status}] {child}.{ccol} -> {parent}.{pcol}: {n} orphan rows")

    # Inventory references are optional, so only check the non-empty ones.
    inv = t["Inventory_Movements"]
    b = inv["batch_reference"].dropna()
    o = inv["order_reference"].dropna()
    nb = int((~b.isin(t["Production_Batches"]["batch_id"])).sum())
    no = int((~o.isin(t["Sales_Orders"]["order_id"])).sum())
    log(f"[{'OK  ' if nb == 0 else 'FAIL'}] Inventory_Movements.batch_reference -> Production_Batches: {nb} orphans")
    log(f"[{'OK  ' if no == 0 else 'FAIL'}] Inventory_Movements.order_reference -> Sales_Orders: {no} orphans")


# --------------------------------------------------------------------------
# CHECK 5: date ranges
# --------------------------------------------------------------------------
DATE_COLUMNS = {
    "Production_Batches": "production_date",
    "Quality_Control": "test_date",
    "Procurement_Orders": "order_date",
    "Sales_Orders": "order_date",
    "Inventory_Movements": "movement_date",
    "Monthly_Expenses": "expense_month",
    "Customer_Feedback": "feedback_date",
    "Equipment_Maintenance": "maintenance_date",
    "Demand_History": "month",
    "Marketing_Campaigns": "start_date",
    "Customers": "first_order_date",
}


def check_dates(t):
    section("CHECK 5: Date ranges (earliest and latest date per table)")
    for name, col in DATE_COLUMNS.items():
        d = pd.to_datetime(t[name][col], errors="coerce")
        bad = int(d.isna().sum())
        log(f"{name:<22} {col:<18} {d.min().date()}  ->  {d.max().date()}   (unreadable dates: {bad})")


# --------------------------------------------------------------------------
# CHECK 6: do the numbers add up?
# --------------------------------------------------------------------------
def check_math(t):
    section("CHECK 6: Calculation checks (tolerance = 0.05 EUR / 0.002)")
    tol = 0.05

    def report(label, bad, total):
        status = "OK  " if bad == 0 else "WARN"
        log(f"[{status}] {label}: {bad} of {total} rows do not match")

    s = t["Sales_Order_Lines"]
    exp = s["quantity_units"] * s["unit_selling_price_eur"] * (1 - s["discount_rate"])
    # unit_selling_price_eur is rounded to 2 decimals in the file, so we allow a
    # small 1% relative difference instead of an exact match.
    rel_err = ((s["net_sales_eur"] - exp) / exp).abs()
    report("net_sales = qty x price x (1 - discount)  [1% tolerance]", int((rel_err > 0.01).sum()), len(s))
    gp = s["net_sales_eur"] - s["estimated_cogs_eur"]
    report("gross_profit = net_sales - cogs", int(((s["gross_profit_eur"] - gp).abs() > tol).sum()), len(s))

    p = t["Production_Batches"]
    report("production_loss = planned - actual",
           int((p["production_loss_litre"] != p["planned_volume_litre"] - p["actual_volume_litre"]).sum()), len(p))
    yr = p["actual_volume_litre"] / p["planned_volume_litre"]
    report("yield_rate = actual / planned", int(((p["yield_rate"] - yr).abs() > 0.002).sum()), len(p))

    po = t["Procurement_Orders"]
    pv = po["quantity_ordered"] * po["unit_cost_eur"]
    report("purchase_value = qty x unit_cost", int(((po["purchase_value_eur"] - pv).abs() > tol).sum()), len(po))
    lt = (pd.to_datetime(po["actual_delivery_date"]) - pd.to_datetime(po["order_date"])).dt.days
    report("lead_time = actual_delivery - order_date", int((po["lead_time_days"] != lt).sum()), len(po))

    # Business facts (these are findings, not errors)
    section("EXTRA: Business facts you should know")
    late = pd.to_datetime(po["actual_delivery_date"]) > pd.to_datetime(po["expected_delivery_date"])
    log(f"Late supplier deliveries: {int(late.sum())} of {len(po)} ({late.mean():.1%})  -> on-time rate {1 - late.mean():.1%}")
    log("Order status mix:   " + str(t["Sales_Orders"]["order_status"].value_counts().to_dict()))
    log("Batch status mix:   " + str(p["batch_status"].value_counts().to_dict()))
    log("QC status mix:      " + str(t["Quality_Control"]["quality_status"].value_counts().to_dict()))
    log(f"Gross margin % (all lines): {s['gross_profit_eur'].sum() / s['net_sales_eur'].sum():.1%}")
    log(f"Average yield rate: {p['yield_rate'].mean():.1%}")
    log(f"Sales lines with quantity <= 0: {int((s['quantity_units'] <= 0).sum())}")

    # Consistency findings between different sheets
    section("EXTRA: Cross-sheet inconsistencies (document these in your README!)")
    po2 = po.assign(late=late)
    calc = po2.groupby("supplier_id")["late"].apply(lambda x: 1 - x.mean())
    stated = t["Suppliers"].set_index("supplier_id")["on_time_delivery_rate"]
    log(f"Avg on-time rate STATED in Suppliers sheet:        {stated.mean():.1%}")
    log(f"Avg on-time rate CALCULATED from Procurement_Orders: {calc.mean():.1%}")
    log("  -> They disagree. For KPIs, use the calculated value (KPI_Glossary formula).")
    m = t["Sales_Orders"].merge(t["Customers"], on="customer_id")
    before = (pd.to_datetime(m["order_date"]) < pd.to_datetime(m["first_order_date"])).mean()
    log(f"Orders placed BEFORE the customer's first_order_date: {before:.1%}")
    log("  -> first_order_date is unreliable; derive it from Sales_Orders if you need it.")


def main():
    log("VELORA BREWING - DATA VALIDATION REPORT")
    tables = load_data_tables()
    check_shapes(tables)
    check_missing(tables)
    check_duplicates(tables)
    check_foreign_keys(tables)
    check_dates(tables)
    check_math(tables)

    REPORT_FILE.parent.mkdir(exist_ok=True)
    REPORT_FILE.write_text("\n".join(LINES), encoding="utf-8")
    log(f"\nReport saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
