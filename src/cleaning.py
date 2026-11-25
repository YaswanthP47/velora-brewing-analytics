"""
cleaning.py  -  STEP 6a: Reusable data-cleaning functions (pandas only).

The pipeline has two layers:

  LAYER 1 - generic cleaners that work on ANY table (so they can be reused):
      convert_types      fix dates, IDs, numbers stored as text, stray spaces
      remove_duplicates  drop repeated rows / repeated IDs
      handle_missing     fill or flag blanks
      flag_outliers      mark unusual values (IQR rule); never deletes rows

  LAYER 2 - Velora business fixes (the data issues we documented):
      first_order_date rebuilt from orders, season rebuilt from the month,
      supplier on-time rate calculated from deliveries, cancelled orders and
      partial / future periods flagged, analysis-ready tables built.

Everything that changes the data is written to a CleanLog, which becomes
reports/cleaning_report.md.
"""

import re

import numpy as np
import pandas as pd

DATA_CUTOFF = pd.Timestamp("2026-10-31")   # last day with real transactions
DATE_NAMES = {"month", "expense_month"}


class CleanLog:
    """Collects one line per cleaning action, so nothing happens silently."""

    def __init__(self):
        self.rows = []

    def add(self, table, step, detail, count):
        self.rows.append({"table": table, "step": step, "detail": detail, "count": int(count)})

    def frame(self):
        return pd.DataFrame(self.rows, columns=["table", "step", "detail", "count"])


def is_date_col(c):
    return c.endswith("_date") or c in DATE_NAMES


def is_id_col(c):
    return c.endswith("_id") or c.endswith("_reference")


def _is_text(s):
    return pd.api.types.is_string_dtype(s) or s.dtype == object


# =====================================================================
# LAYER 1: generic cleaners
# =====================================================================
def convert_types(df, table="table", log=None, dayfirst=False):
    """Dates -> datetime, IDs -> trimmed UPPER text, numbers-as-text -> numbers, tidy spaces.
    dayfirst=True reads 01/02/2025 as 1 February (European); False reads it as 2 January."""
    log = log or CleanLog()
    df = df.copy()
    for c in df.columns:
        if is_date_col(c):
            if not pd.api.types.is_datetime64_any_dtype(df[c]):
                before = df[c].isna().sum()
                try:
                    df[c] = pd.to_datetime(df[c], errors="coerce", format="mixed", dayfirst=dayfirst)
                except (TypeError, ValueError):
                    df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=dayfirst)
                log.add(table, "type conversion", f"{c}: converted to date", len(df))
                bad = df[c].isna().sum() - before
                if bad:
                    log.add(table, "type conversion", f"{c}: unreadable dates set to missing", bad)
        elif is_id_col(c):
            fixed = df[c].map(lambda v: v.strip().upper() if isinstance(v, str) else v)
            changed = ((fixed != df[c]) & df[c].notna()).sum()
            if changed:
                log.add(table, "type conversion", f"{c}: IDs trimmed / upper-cased", changed)
            df[c] = fixed
        elif _is_text(df[c]):
            tidy = df[c].map(lambda v: re.sub(r"\s+", " ", v.strip()) if isinstance(v, str) else v)
            # numbers stored as text, e.g. "EUR 1,234.50" or "12%"
            # Only currency signs, thousands commas, spaces and % are allowed around a number.
            # (Anything else, like 'Customer_0001' or '500ml bottle', is real text and stays text.)
            as_num = pd.to_numeric(tidy.map(lambda v: re.sub(r"(EUR|USD|[\u20ac$\u00a3%,\s])", "", v, flags=re.I)
                                            if isinstance(v, str) else v), errors="coerce")
            non_null = tidy.notna().sum()
            if non_null and as_num.notna().sum() / non_null >= 0.95 and non_null > 5:
                df[c] = as_num
                log.add(table, "type conversion", f"{c}: text converted to number", non_null)
                continue
            changed = ((tidy != df[c]) & df[c].notna()).sum()
            if changed:
                log.add(table, "type conversion", f"{c}: extra spaces removed", changed)
            df[c] = tidy
            if 1 < df[c].nunique() <= 15:        # same word in different CASE -> one spelling
                counts = df[c].value_counts()
                best = {}
                for v in counts.index:             # most frequent spelling wins
                    best.setdefault(v.lower(), v)
                harm = df[c].map(lambda v: best.get(v.lower(), v) if isinstance(v, str) else v)
                n = (harm != df[c]).sum()
                if n:
                    log.add(table, "type conversion", f"{c}: inconsistent upper/lower case unified", n)
                df[c] = harm
    return df


def remove_duplicates(df, table="table", log=None, key=None, business_key=None):
    """Drop fully identical rows and repeated primary keys. Business-key repeats are only reported."""
    log = log or CleanLog()
    full = int(df.duplicated().sum())
    df = df.drop_duplicates()
    if full:
        log.add(table, "duplicates", "identical rows removed", full)
    if key:
        k = int(df.duplicated(subset=key).sum())
        df = df.drop_duplicates(subset=key, keep="first")
        if k:
            log.add(table, "duplicates", f"repeated {key} removed (first kept)", k)
    if business_key:
        b = int(df.duplicated(subset=business_key).sum())
        if b:
            log.add(table, "duplicates", f"duplicate-like records on {business_key} (reported, kept)", b)
    return df


def handle_missing(df, table="table", log=None, key=None, keep_empty=(), group=None):
    """Rows with no primary key are dropped. Numbers get the median (per group if given),
    text gets 'Unknown', dates stay missing. Every filled number gets a *_was_missing flag."""
    log = log or CleanLog()
    df = df.copy()
    if key:
        n = int(df[key].isna().sum())
        if n:
            df = df[df[key].notna()]
            log.add(table, "missing values", f"rows without {key} dropped", n)
    for c in df.columns:
        n = int(df[c].isna().sum())
        if n == 0 or c in keep_empty or is_id_col(c):
            continue
        if is_date_col(c):
            log.add(table, "missing values", f"{c}: dates left missing (cannot be invented)", n)
        elif pd.api.types.is_numeric_dtype(df[c]):
            df[c + "_was_missing"] = df[c].isna()
            fill = df.groupby(group)[c].transform("median") if group and group in df.columns else df[c].median()
            df[c] = df[c].fillna(fill).fillna(df[c].median())
            log.add(table, "missing values", f"{c}: filled with {'group ' if group else ''}median", n)
        else:
            df[c] = df[c].fillna("Unknown")
            log.add(table, "missing values", f"{c}: filled with 'Unknown'", n)
    return df


def flag_outliers(df, col, group=None, k=1.5):
    """True where a value lies outside Q1-k*IQR .. Q3+k*IQR (inside its group if given)."""
    if group is None:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        return (df[col] < q1 - k * iqr) | (df[col] > q3 + k * iqr)
    q1 = df.groupby(group)[col].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby(group)[col].transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    return (df[col] < q1 - k * iqr) | (df[col] > q3 + k * iqr)


# =====================================================================
# LAYER 2: Velora business fixes
# =====================================================================
PRIMARY_KEYS = {
    "Product_Master": "product_id", "Raw_Materials": "material_id", "Suppliers": "supplier_id",
    "Employees": "employee_id", "Distributors": "distributor_id", "Customers": "customer_id",
    "Marketing_Campaigns": "campaign_id", "Production_Batches": "batch_id", "Quality_Control": "qc_test_id",
    "Procurement_Orders": "po_id", "Sales_Orders": "order_id", "Sales_Order_Lines": "order_line_id",
    "Inventory_Movements": "movement_id", "Monthly_Expenses": "expense_id",
    "Customer_Feedback": "feedback_id", "Equipment_Maintenance": "maintenance_id",
}
BUSINESS_KEYS = {
    "Sales_Order_Lines": ["order_id", "product_id"],
    "Production_Batches": ["production_date", "product_id", "production_line"],
    "Procurement_Orders": ["order_date", "supplier_id", "material_id", "quantity_ordered"],
    "Customer_Feedback": ["feedback_date", "customer_id", "product_id", "feedback_text"],
    "Demand_History": ["month", "product_id"],
}
EXPECTED_EMPTY = {"Inventory_Movements": ("batch_reference", "order_reference")}

# (table, column, group column or None) -> outliers are judged INSIDE the group
OUTLIER_SPEC = [
    ("sales_lines", "quantity_units", "sales_channel"), ("sales_lines", "unit_selling_price_eur", "product_id"),
    ("sales_lines", "discount_rate", None), ("sales_lines", "net_sales_eur", "sales_channel"),
    ("batches_qc", "yield_rate", "product_id"), ("batches_qc", "planned_volume_litre", None),
    ("batches_qc", "estimated_batch_cost_eur", None), ("batches_qc", "defect_units", None),
    ("batches_qc", "ph_value", None), ("batches_qc", "temperature_c", None),
    ("procurement", "quantity_ordered", "material_id"), ("procurement", "unit_cost_eur", "material_id"),
    ("procurement", "purchase_value_eur", "material_id"), ("procurement", "lead_time_days", "supplier_id"),
    ("Equipment_Maintenance", "downtime_hours", "maintenance_type"),
    ("Equipment_Maintenance", "maintenance_cost_eur", "maintenance_type"),
    ("Monthly_Expenses", "amount_eur", "expense_category"),
    ("demand", "units_sold", "product_id"),
    ("Marketing_Campaigns", "spend_eur", "channel"), ("Marketing_Campaigns", "clicks", "channel"),
]


def season_from_month(m):
    """Northern-hemisphere (meteorological) season: Dec-Feb Winter, Mar-May Spring, Jun-Aug Summer, Sep-Nov Autumn."""
    return m.map(lambda x: "Winter" if x in (12, 1, 2) else "Spring" if x in (3, 4, 5)
                 else "Summer" if x in (6, 7, 8) else "Autumn")


def clean_generic(raw, log):
    """Run the four generic cleaners on every raw table."""
    out = {}
    for name, df in raw.items():
        df = convert_types(df, name, log)
        df = remove_duplicates(df, name, log, key=PRIMARY_KEYS.get(name), business_key=BUSINESS_KEYS.get(name))
        df = handle_missing(df, name, log, key=PRIMARY_KEYS.get(name), keep_empty=EXPECTED_EMPTY.get(name, ()))
        out[name] = df.reset_index(drop=True)
    return out


def apply_business_rules(t, log):
    """Fix the documented issues and build the analysis-ready tables."""
    t = dict(t)
    pm = t["Product_Master"].set_index("product_id")

    # --- Customers: first_order_date rebuilt from the orders themselves
    orders = t["Sales_Orders"].copy()
    first = orders.groupby("customer_id")["order_date"].min()
    cust = t["Customers"].copy()
    cust["first_order_date_stated"] = cust["first_order_date"]
    cust["first_order_date"] = cust["customer_id"].map(first)
    changed = (cust["first_order_date"] != cust["first_order_date_stated"]).sum()
    log.add("Customers", "business rule", "first_order_date rebuilt from Sales_Orders (stated one kept as *_stated)", changed)
    log.add("Customers", "business rule", "customers with no orders (first_order_date left missing)", cust["first_order_date"].isna().sum())
    t["Customers"] = cust

    # --- Orders: flags
    orders["is_cancelled"] = orders["order_status"] == "Cancelled"
    orders["year"] = orders["order_date"].dt.year
    orders["month_no"] = orders["order_date"].dt.month
    orders["is_partial_year"] = orders["order_date"].dt.year == DATA_CUTOFF.year
    log.add("Sales_Orders", "business rule", "is_cancelled flag added (revenue excludes these)", orders["is_cancelled"].sum())
    t["Sales_Orders"] = orders

    # --- Demand history: season rebuilt, future months flagged
    dh = t["Demand_History"].copy()
    dh["season_stated"] = dh["season"]
    dh["season"] = season_from_month(dh["month"].dt.month)
    log.add("Demand_History", "business rule", "season rebuilt from month (stated one kept as *_stated)", (dh["season"] != dh["season_stated"]).sum())
    dh["year"], dh["month_no"] = dh["month"].dt.year, dh["month"].dt.month
    dh["is_forecast_period"] = dh["month"] > DATA_CUTOFF
    log.add("Demand_History", "business rule", "rows after 2026-10-31 flagged is_forecast_period", dh["is_forecast_period"].sum())
    t["demand"] = dh

    # --- Procurement: delay, late flag, material category; supplier on-time rate calculated
    po = t["Procurement_Orders"].copy()
    po["delay_days"] = (po["actual_delivery_date"] - po["expected_delivery_date"]).dt.days
    po["is_late"] = po["delay_days"] > 0
    po["material_category"] = po["material_id"].map(t["Raw_Materials"].set_index("material_id")["category"])
    t["procurement"] = po
    sup = t["Suppliers"].copy()
    calc = po.groupby("supplier_id")["is_late"].agg(lambda s: 1 - s.mean())
    sup = sup.rename(columns={"on_time_delivery_rate": "on_time_rate_stated", "main_category": "main_category_stated"})
    sup["on_time_rate_calc"] = sup["supplier_id"].map(calc)
    sup["n_deliveries"] = sup["supplier_id"].map(po.groupby("supplier_id").size())
    log.add("Suppliers", "business rule", "on_time_rate_calc added from deliveries (stated rate kept as *_stated)", len(sup))
    log.add("Suppliers", "business rule", "main_category renamed main_category_stated (unreliable, see known issue 3)", len(sup))
    t["Suppliers"] = sup

    # --- Sales lines: one wide, analysis-ready table
    sl = t["Sales_Order_Lines"].merge(
        orders[["order_id", "order_date", "customer_id", "distributor_id", "sales_channel", "ship_to_country",
                "order_status", "is_cancelled", "year", "month_no", "is_partial_year"]], on="order_id", how="left")
    sl["product_name"] = sl["product_id"].map(pm["product_name"])
    sl = sl.merge(cust[["customer_id", "customer_type", "account_size"]], on="customer_id", how="left")
    sl["net_sales_counted_eur"] = np.where(sl["is_cancelled"], 0.0, sl["net_sales_eur"])
    sl["gross_profit_counted_eur"] = np.where(sl["is_cancelled"], 0.0, sl["gross_profit_eur"])
    log.add("sales_lines", "business rule", "order lines joined with order, product and customer info", len(sl))
    t["sales_lines"] = sl

    # --- Batches + QC: one table, one row per batch
    b = t["Production_Batches"].merge(t["Quality_Control"].drop(columns=["test_date"]), on="batch_id", how="left")
    b["product_name"] = b["product_id"].map(pm["product_name"])
    b["target_yield_rate"] = b["product_id"].map(pm["target_yield_rate"])
    b["yield_gap"] = b["yield_rate"] - b["target_yield_rate"]
    b["is_review"] = b["quality_status"] == "Review"
    b["year"], b["month_no"] = b["production_date"].dt.year, b["production_date"].dt.month
    b["is_partial_year"] = b["year"] == DATA_CUTOFF.year
    log.add("batches_qc", "business rule", "batches joined with their QC test, product target and is_review flag", len(b))
    t["batches_qc"] = b

    # --- Feedback
    fb = t["Customer_Feedback"].copy()
    fb["is_negative"] = fb["sentiment_label"] == "Negative"
    fb["is_complaint"] = fb["feedback_type"] == "Complaint"
    t["Customer_Feedback"] = fb
    return t


def add_outlier_flags(t, log, k=1.5):
    """Add <col>_outlier flags (IQR rule, within group). Returns a summary table. Rows are NEVER deleted."""
    rows = []
    for table, col, group in OUTLIER_SPEC:
        df = t[table]
        flag = flag_outliers(df, col, group, k)
        df[col + "_outlier"] = flag
        rows.append({"table": table, "column": col, "judged_within": group or "all rows",
                     "flagged": int(flag.sum()), "share_pct": round(100 * flag.mean(), 2), "rows": len(df)})
    return pd.DataFrame(rows)


def check_results(t):
    """After cleaning: do the numbers still add up? Returns (description, passed) pairs."""
    sl, b, po = t["sales_lines"], t["batches_qc"], t["procurement"]
    rel = ((sl["quantity_units"] * sl["unit_selling_price_eur"] * (1 - sl["discount_rate"]) - sl["net_sales_eur"]) / sl["net_sales_eur"]).abs()
    return [
        ("every primary key is unique", all(t[n][k].is_unique for n, k in PRIMARY_KEYS.items())),
        ("net_sales = qty x price x (1 - discount), within 1%", bool((rel < 0.01).all())),
        ("production_loss = planned - actual", bool((b["planned_volume_litre"] - b["actual_volume_litre"] == b["production_loss_litre"]).all())),
        ("lead_time_days = actual delivery - order date", bool(((po["actual_delivery_date"] - po["order_date"]).dt.days == po["lead_time_days"]).all())),
        ("every sales line has an order, product and customer", bool(sl[["order_date", "product_name", "customer_type"]].notna().all().all())),
        ("every batch has a QC result", bool(b["quality_status"].notna().all())),
        ("no order is dated before its customer's rebuilt first_order_date",
         bool((t["Sales_Orders"].merge(t["Customers"], on="customer_id")
               .pipe(lambda m: (m["order_date"] >= m["first_order_date"]).all())))),
        ("season matches the calendar month in every Demand_History row",
         bool((t["demand"]["season"] == season_from_month(t["demand"]["month"].dt.month)).all())),
    ]


def clean_all(raw):
    """THE PIPELINE: raw tables in, (clean tables, log table, outlier table, checks) out."""
    log = CleanLog()
    t = clean_generic(raw, log)
    t = apply_business_rules(t, log)
    outliers = add_outlier_flags(t, log)
    return t, log.frame(), outliers, check_results(t)
