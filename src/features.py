"""
features.py  -  STEP 7d: Feature engineering (turning clean tables into model-ready inputs).

A FEATURE is a column a model can learn from. Good features carry domain knowledge:
    lag features        "what happened last month?"        (units_lag1, units_lag12)
    rolling features    "what is the recent average?"      (units_roll_mean_3)
    calendar features   "which month is it?"               (month_sin, month_cos, seasonal_index)
    yield & margin      production and profit behaviour    (yield_gap, margin_pct, price_realisation)
    RFM                 customer value: Recency, Frequency, Monetary

LEAKAGE RULE (the most important rule in this file): a feature for time t may use ONLY information
known BEFORE t. Every lag and rolling feature is therefore shifted by one period, and the seasonal
index is learned from the training years only. src/test_features.py checks this automatically.
"""

import numpy as np
import pandas as pd

import stats_utils as su
from cleaning import DATA_CUTOFF

TRAIN_END = pd.Timestamp("2025-12-31")      # same split as preprocess.py: train 2023-2025, test 2026
FIRST_MONTH = pd.Timestamp("2023-01-01")


# ====================================================================== demand
def demand_features(clean, train_end=TRAIN_END, lags=(1, 2, 3, 6, 12)):
    """One row per product and month (real history only). Target: units_sold."""
    d = clean["demand"]
    d = d[~d["is_forecast_period"]].sort_values(["product_id", "month"]).copy()
    pm = clean["Product_Master"].set_index("product_id")

    g = d.groupby("product_id")["units_sold"]
    for k in lags:
        d[f"units_lag{k}"] = g.shift(k)
    past = g.shift(1)                                           # everything below uses ONLY past months
    for w in (3, 6, 12):
        d[f"units_roll_mean_{w}"] = past.groupby(d["product_id"]).transform(lambda s, w=w: s.rolling(w).mean())
    d["units_roll_std_3"] = past.groupby(d["product_id"]).transform(lambda s: s.rolling(3).std())
    d["promo_lag1"] = d.groupby("product_id")["promotion_discount_rate"].shift(1)

    d["time_index"] = (d["year"] - FIRST_MONTH.year) * 12 + d["month_no"] - 1
    d["month_sin"] = np.sin(2 * np.pi * d["month_no"] / 12)
    d["month_cos"] = np.cos(2 * np.pi * d["month_no"] / 12)
    d["quarter"] = (d["month_no"] - 1) // 3 + 1

    total = d.groupby("month")["units_sold"].sum()
    d["total_units_lag1"] = d["month"].map(total.shift(1))
    index, *_ = su.seasonal_profile(total[total.index <= train_end])   # learned from TRAINING years only
    d["seasonal_index"] = d["month_no"].map(index)

    for col in ["wholesale_price_eur", "abv_percent", "unit_variable_cost_eur"]:
        d[col] = d["product_id"].map(pm[col])
    d["months_since_launch"] = ((d["month"] - d["product_id"].map(pm["launch_date"])).dt.days / 30.44).round(1)
    d["has_full_history"] = d["units_lag12"].notna()
    return d.reset_index(drop=True)


# ====================================================================== quality control
def qc_features(clean):
    """One row per batch. Target: is_review."""
    b = clean["batches_qc"].sort_values(["production_date", "batch_id"]).copy()
    abv = clean["Product_Master"].set_index("product_id")["abv_percent"]
    b["loss_pct"] = b["production_loss_litre"] / b["planned_volume_litre"] * 100
    b["cost_per_litre"] = b["estimated_batch_cost_eur"] / b["actual_volume_litre"]
    b["abv_deviation"] = b["measured_abv_percent"] - b["product_id"].map(abv)
    b["abs_abv_deviation"] = b["abv_deviation"].abs()
    b["defects_per_1000L"] = b["defect_units"] / b["actual_volume_litre"] * 1000
    g = b.groupby("production_line")
    b["days_since_prev_batch_line"] = g["production_date"].diff().dt.days
    b["is_review_num"] = b["is_review"].astype(float)
    b["prev_batch_review_line"] = b.groupby("production_line")["is_review_num"].shift(1)
    b["review_rate_prev10_line"] = b.groupby("production_line")["is_review_num"].transform(lambda s: s.shift(1).rolling(10).mean())
    b["prev_yield_line"] = g["yield_rate"].shift(1)
    b["yield_roll5_prev_line"] = g["yield_rate"].transform(lambda s: s.shift(1).rolling(5).mean())
    cols = ["batch_id", "production_date", "product_name", "production_line", "batch_status", "month_no", "year",
            "planned_volume_litre", "yield_rate", "yield_gap", "loss_pct", "cost_per_litre", "shift_count",
            "temperature_c", "ph_value", "specific_gravity", "measured_abv_percent", "colour_ebc", "defect_units",
            "abv_deviation", "abs_abv_deviation", "defects_per_1000L", "days_since_prev_batch_line",
            "prev_batch_review_line", "review_rate_prev10_line", "prev_yield_line", "yield_roll5_prev_line", "is_review"]
    return b[cols].reset_index(drop=True)


# ====================================================================== yield and margin by product and month
def product_month_features(clean):
    """One row per product and month: production (yield) and sales (margin) side by side."""
    sl = clean["sales_lines"]
    pm = clean["Product_Master"].set_index("product_id")
    sl = sl.assign(month=sl["order_date"].dt.to_period("M").dt.to_timestamp(),
                   list_value=sl["quantity_units"] * sl["product_id"].map(pm["wholesale_price_eur"]),
                   sold_value=sl["quantity_units"] * sl["unit_selling_price_eur"],
                   online_units=np.where(sl["sales_channel"] == "Online", sl["quantity_units"], 0))
    cancel = sl.groupby(["product_id", "month"])["is_cancelled"].mean().rename("cancel_rate_lines")
    ok = sl[~sl["is_cancelled"]]
    s = ok.groupby(["product_id", "month"]).agg(
        net_sales_eur=("net_sales_eur", "sum"), gross_profit_eur=("gross_profit_eur", "sum"),
        units=("quantity_units", "sum"), sold_value=("sold_value", "sum"), list_value=("list_value", "sum"),
        online_units=("online_units", "sum"), avg_discount=("discount_rate", "mean"))
    s["margin_pct"] = s["gross_profit_eur"] / s["net_sales_eur"] * 100
    s["price_realisation"] = s["sold_value"] / s["list_value"]               # 1.00 = sold at list price
    s["online_share_units"] = s["online_units"] / s["units"]
    s = s.drop(columns=["sold_value", "list_value", "online_units"]).join(cancel)

    b = clean["batches_qc"].assign(month=lambda x: x["production_date"].dt.to_period("M").dt.to_timestamp())
    p = b.groupby(["product_id", "month"]).agg(
        n_batches=("batch_id", "count"), volume_litre=("actual_volume_litre", "sum"),
        yield_mean=("yield_rate", "mean"), yield_gap_mean=("yield_gap", "mean"),
        loss_litre=("production_loss_litre", "sum"), review_rate=("is_review", "mean"))
    out = s.join(p, how="left").reset_index().sort_values(["product_id", "month"])
    out["has_batch"] = out["n_batches"].notna()
    out["n_batches"] = out["n_batches"].fillna(0)
    gm = out.groupby("product_id")["margin_pct"]
    out["margin_pct_lag1"] = gm.shift(1)
    out["margin_roll3_prev"] = gm.transform(lambda x: x.shift(1).rolling(3).mean())
    out["product_name"] = out["product_id"].map(pm["product_name"])
    return out.reset_index(drop=True)


# ====================================================================== customers (RFM)
def customer_features(clean, as_of=DATA_CUTOFF):
    """One row per customer, as of the data cutoff. Used for segmentation (clustering)."""
    o, sl = clean["Sales_Orders"], clean["sales_lines"]
    ok_o = o[~o["is_cancelled"]]
    freq = ok_o.groupby("customer_id").agg(frequency=("order_id", "count"), first_order=("order_date", "min"), last_order=("order_date", "max"))
    rev = sl[~sl["is_cancelled"]].groupby("customer_id").agg(
        monetary=("net_sales_eur", "sum"), units=("quantity_units", "sum"),
        avg_discount=("discount_rate", "mean"), n_products=("product_id", "nunique"))
    allo = o.groupby("customer_id").agg(orders_total=("order_id", "count"), cancel_rate=("is_cancelled", "mean"),
                                        online_order_share=("sales_channel", lambda s: (s == "Online").mean()))
    c = clean["Customers"].set_index("customer_id")[["customer_type", "country", "account_size"]]
    f = c.join(freq).join(rev).join(allo)
    f["recency_days"] = (as_of - f["last_order"]).dt.days
    f["tenure_days"] = (as_of - f["first_order"]).dt.days
    f["avg_order_value"] = f["monetary"] / f["frequency"]
    f["has_orders"] = f["frequency"].notna()
    return f.drop(columns=["first_order", "last_order"]).reset_index()


# ====================================================================== suppliers
def supplier_features(clean):
    """One row per supplier, from delivery behaviour."""
    po = clean["procurement"]
    g = po.groupby("supplier_id")
    f = g.agg(n_orders=("po_id", "count"), late_share=("is_late", "mean"), avg_delay_days=("delay_days", "mean"),
              avg_lead_time_days=("lead_time_days", "mean"), lead_time_std=("lead_time_days", "std"),
              total_spend_eur=("purchase_value_eur", "sum"), n_materials=("material_id", "nunique"))
    f["delay_p90_days"] = g["delay_days"].quantile(0.9)
    f["spend_share"] = f["total_spend_eur"] / f["total_spend_eur"].sum()
    s = clean["Suppliers"].set_index("supplier_id")
    f["on_time_rate_stated"] = s["on_time_rate_stated"]
    f["on_time_rate_calc"] = 1 - f["late_share"]
    f["rate_gap"] = f["on_time_rate_stated"] - f["on_time_rate_calc"]
    f["supplier_name"] = s["supplier_name"]
    return f.reset_index()


def build_all(clean, train_end=TRAIN_END):
    return {"demand_features": demand_features(clean, train_end), "qc_features": qc_features(clean),
            "product_month_features": product_month_features(clean), "customer_features": customer_features(clean),
            "supplier_features": supplier_features(clean)}


# ---- one-line definition per engineered feature (used for the feature report) ----
FEATURE_DOC = [
    ("demand_features", "units_lag1 / 2 / 3 / 6 / 12", "Units sold 1, 2, 3, 6 or 12 months earlier (same product)", "past only"),
    ("demand_features", "units_roll_mean_3 / 6 / 12", "Average units of the previous 3, 6 or 12 months", "shifted by 1 month"),
    ("demand_features", "units_roll_std_3", "Spread of the previous 3 months (how unstable demand is)", "shifted by 1 month"),
    ("demand_features", "promo_lag1", "Last month's promotion discount", "past only"),
    ("demand_features", "month_sin, month_cos", "Month as a circle, so December and January are neighbours", "calendar"),
    ("demand_features", "seasonal_index", "Typical % above/below an average month, learned from 2023-2025 totals", "training years only"),
    ("demand_features", "total_units_lag1", "All products' demand in the previous month", "past only"),
    ("demand_features", "time_index", "Months since January 2023 (captures the upward trend)", "calendar"),
    ("demand_features", "months_since_launch", "Age of the product in months", "calendar"),
    ("demand_features", "has_full_history", "True once 12 months of lags exist (use for model training)", "flag"),
    ("qc_features", "loss_pct", "Production loss as % of planned volume", "same batch"),
    ("qc_features", "cost_per_litre", "Batch cost / litres produced", "same batch"),
    ("qc_features", "abv_deviation, abs_abv_deviation", "Measured alcohol minus the product's intended ABV", "same batch"),
    ("qc_features", "defects_per_1000L", "Defect units per 1,000 litres", "same batch"),
    ("qc_features", "days_since_prev_batch_line", "Days since the previous batch on the same line", "past only"),
    ("qc_features", "prev_batch_review_line", "Was the previous batch on this line sent to Review (1/0)?", "past only"),
    ("qc_features", "review_rate_prev10_line", "Review share of the last 10 batches on this line", "shifted by 1 batch"),
    ("qc_features", "prev_yield_line, yield_roll5_prev_line", "Previous yield and 5-batch average yield on this line", "shifted by 1 batch"),
    ("product_month_features", "margin_pct", "Gross profit / net sales for the product in the month", "same month"),
    ("product_month_features", "price_realisation", "Average price sold at / wholesale list price (1.00 = list price)", "same month"),
    ("product_month_features", "avg_discount, online_share_units, cancel_rate_lines", "Discount level, share of units sold online, share of lines cancelled", "same month"),
    ("product_month_features", "yield_mean, yield_gap_mean, loss_litre, review_rate", "Production side of the same product and month (empty if no batch)", "same month"),
    ("product_month_features", "margin_pct_lag1, margin_roll3_prev", "Previous month's margin and previous 3-month average", "past only"),
    ("customer_features", "recency_days", "Days from the customer's last order to 2026-10-31", "as of cutoff"),
    ("customer_features", "frequency, monetary, avg_order_value", "Number of orders, total net sales, net sales per order (cancelled excluded)", "as of cutoff"),
    ("customer_features", "tenure_days", "Days from the first order to 2026-10-31 (rebuilt first_order_date)", "as of cutoff"),
    ("customer_features", "cancel_rate, online_order_share, n_products, avg_discount", "Behaviour measures per customer", "as of cutoff"),
    ("supplier_features", "late_share, avg_delay_days, delay_p90_days", "How often and how late the supplier delivers", "all history"),
    ("supplier_features", "lead_time_std", "Variation of lead time (reliability)", "all history"),
    ("supplier_features", "rate_gap", "Stated minus calculated on-time rate", "all history"),
]
