"""
generate_synthetic_data.py  -  STEP 4a: Reproducible synthetic data generator.

Run from the project folder:
        python src/generate_synthetic_data.py                 # default: seed 42
        python src/generate_synthetic_data.py --seed 7        # different random data
        python src/generate_synthetic_data.py --scale 0.5     # half the rows

"Reproducible" means: the SAME seed always gives the SAME data.

It creates CSV files in data/synthetic/ for these areas (same column names as
the original Excel file):
    reference : Product_Master, Raw_Materials, Suppliers, Distributors, Customers
    production: Production_Batches, Quality_Control
    supply    : Procurement_Orders
    sales     : Sales_Orders, Sales_Order_Lines
    feedback  : Customer_Feedback

All assumptions are written next to the code that uses them (ASSUMPTION: ...)
and summarised in docs/data_model.md.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path("data/synthetic")
ORIGINAL_FILE = Path("data/raw/Velora_Brewing_End_to_End_Data_Science_Dataset.xlsx")

START = pd.Timestamp("2023-01-01")
END = pd.Timestamp("2026-10-31")
COUNTRIES = ["Slovenia", "Germany", "Croatia", "Hungary", "Italy", "Czechia", "Austria"]

# ---------------------------------------------------------------- master data
# (id, name, style, abv %, variable cost EUR/unit, wholesale price EUR, retail price, target yield, launch date)
PRODUCTS = [
    ("VLR001", "Velora Classic Lager", "Lager", 4.8, 0.50, 1.35, 2.20, 0.92, "2023-01-01"),
    ("VLR002", "Alpine Gold", "Premium Lager", 5.2, 0.52, 1.55, 2.55, 0.90, "2023-01-01"),
    ("VLR003", "Maribor Dark", "Dark Lager", 5.0, 0.48, 1.60, 2.70, 0.88, "2023-01-01"),
    ("VLR004", "Baltic Wheat", "Wheat Beer", 5.1, 0.53, 1.50, 2.50, 0.89, "2023-01-01"),
    ("VLR005", "Forest Pilsner", "Pilsner", 4.9, 0.51, 1.45, 2.40, 0.91, "2023-01-01"),
    ("VLR006", "Crimson Amber", "Amber Ale", 5.4, 0.55, 1.75, 2.90, 0.87, "2023-01-01"),
    ("VLR007", "Midnight Stout", "Stout", 6.0, 0.57, 1.95, 3.20, 0.85, "2023-01-01"),
    ("VLR008", "Citrus Wave", "Fruit Beer", 4.5, 0.49, 1.70, 2.85, 0.88, "2023-01-01"),
    ("VLR009", "Honey Valley", "Honey Ale", 5.3, 0.54, 1.85, 3.05, 0.86, "2023-07-01"),
    ("VLR010", "Royal Reserve", "Strong Lager", 7.2, 0.60, 2.05, 3.40, 0.84, "2023-07-01"),
    ("VLR011", "Zero Horizon", "Non-alcoholic", 0.5, 0.45, 1.25, 2.10, 0.94, "2023-07-01"),
    ("VLR012", "Alpine IPA", "India Pale Ale", 6.2, 0.56, 2.00, 3.35, 0.86, "2023-07-01"),
    ("VLR013", "Summer Berry", "Fruit Ale", 4.2, 0.47, 1.65, 2.75, 0.89, "2023-07-01"),
]
MATERIALS = [
    ("RM001", "Pilsner Malt", "kg", "Malt", 1.25), ("RM002", "Wheat Malt", "kg", "Malt", 1.45),
    ("RM003", "Roasted Barley", "kg", "Malt", 1.80), ("RM004", "Hops - Saaz", "kg", "Hops", 12.5),
    ("RM005", "Hops - Cascade", "kg", "Hops", 14.2), ("RM006", "Brewer's Yeast", "kg", "Yeast", 8.5),
    ("RM007", "Fruit Concentrate", "litre", "Flavouring", 3.8), ("RM008", "Honey", "kg", "Flavouring", 5.2),
    ("RM009", "Water Treatment Salts", "kg", "Process", 2.1), ("RM010", "Glass Bottle 500ml", "unit", "Packaging", 0.18),
    ("RM011", "Aluminium Can 500ml", "unit", "Packaging", 0.16), ("RM012", "Printed Label", "unit", "Packaging", 0.04),
    ("RM013", "Cardboard Case", "unit", "Packaging", 0.35), ("RM014", "Cleaning Chemical", "litre", "Process", 2.7),
]
# ASSUMPTION: each supplier's main_category matches its name AND the raw-material
# category it delivers (the original file does not guarantee this).
SUPPLIERS = [
    ("Danube Malt Co", "Hungary", "Malt"), ("Alpine Hops GmbH", "Austria", "Hops"),
    ("Adria Packaging", "Germany", "Packaging"), ("GreenYeast Labs", "Germany", "Yeast"),
    ("Baltic Glassworks", "Austria", "Packaging"), ("Central Grain Partners", "Czechia", "Malt"),
    ("PureSpring Ingredients", "Austria", "Process"), ("EuroCan Systems", "Czechia", "Packaging"),
    ("Valley Honey Cooperative", "Germany", "Flavouring"), ("Saaz Botanicals", "Czechia", "Hops"),
    ("Maribor Labels", "Hungary", "Packaging"), ("Nordic Process Supply", "Slovenia", "Process"),
    ("Carpathian Malt", "Hungary", "Malt"), ("BlueRiver Logistics", "Hungary", "Process"),
    ("Amber Ingredients", "Germany", "Flavouring"), ("Prague Bottle Works", "Hungary", "Packaging"),
    ("Sava Agricultural Supply", "Austria", "Malt"), ("CitrusCraft Europe", "Austria", "Flavouring"),
    ("Eastern Yeast Company", "Italy", "Yeast"), ("EcoPack Slovenia", "Hungary", "Packaging"),
]
# ASSUMPTION: feedback_text fully determines sentiment AND issue_category
# (in the original file issue_category is random, which hurts NLP learning).
FEEDBACK = [
    ("Bottle cap was damaged on arrival", "Negative", "Packaging"),
    ("Can label was difficult to read", "Negative", "Packaging"),
    ("Some bottles were leaking", "Negative", "Packaging"),
    ("Delivery arrived later than the agreed date", "Negative", "Delivery"),
    ("The product was warm when delivered", "Negative", "Delivery"),
    ("Several units were missing from the shipment", "Negative", "Order Accuracy"),
    ("Taste was different from the previous order", "Negative", "Product Quality"),
    ("Order quantity did not match invoice", "Neutral", "Order Accuracy"),
    ("Customer liked the new seasonal flavour", "Positive", "Product Quality"),
    ("Product quality was consistent and satisfactory", "Positive", "Product Quality"),
    ("Packaging was excellent and product arrived on time", "Positive", "Packaging"),
    ("Distributor support team responded quickly", "Positive", "Customer Service"),
]


def random_dates(rng, n, start=START, end=END):
    """n random dates between start and end (inclusive)."""
    days = (end - start).days
    return start + pd.to_timedelta(rng.integers(0, days + 1, n), unit="D")


def launched(date):
    """Products already on sale at a given date."""
    return [p for p in PRODUCTS if pd.Timestamp(p[8]) <= date]


# ---------------------------------------------------------------- generators
def gen_reference(rng, scale):
    product = pd.DataFrame(PRODUCTS, columns=[
        "product_id", "product_name", "beer_style", "abv_percent", "unit_variable_cost_eur",
        "wholesale_price_eur", "suggested_retail_price_eur", "target_yield_rate", "launch_date"])
    product.insert(8, "pack_size_litre", 0.5)
    product.insert(9, "pack_format", "500ml bottle")
    product["status"] = "Active"
    product = product[["product_id", "product_name", "beer_style", "abv_percent", "unit_variable_cost_eur",
                       "wholesale_price_eur", "suggested_retail_price_eur", "target_yield_rate",
                       "pack_size_litre", "pack_format", "launch_date", "status"]]

    materials = pd.DataFrame(MATERIALS, columns=[
        "material_id", "material_name", "unit", "category", "standard_unit_cost_eur"])

    n_sup = len(SUPPLIERS)
    status = np.array(["Approved"] * 15 + ["Under Review"] * 5)
    rng.shuffle(status)
    suppliers = pd.DataFrame({
        "supplier_id": [f"SUP{i + 1:03d}" for i in range(n_sup)],
        "supplier_name": [s[0] for s in SUPPLIERS],
        "country": [s[1] for s in SUPPLIERS],
        "main_category": [s[2] for s in SUPPLIERS],
        # ASSUMPTION: average lead time 2-18 days, stated on-time rate 82%-97%
        "average_lead_time_days": rng.uniform(2, 18, n_sup).round(1),
        "on_time_delivery_rate": rng.uniform(0.82, 0.97, n_sup).round(2),
        "supplier_status": status,
    })

    n_dist = 35
    distributors = pd.DataFrame({
        "distributor_id": [f"DST{i + 1:03d}" for i in range(n_dist)],
        "distributor_name_alias": [f"Distributor_{i + 1:02d}" for i in range(n_dist)],
        "country": rng.choice(COUNTRIES, n_dist),
        "channel_type": rng.choice(["Retail", "National", "Regional", "Hospitality"], n_dist,
                                   p=[13 / 35, 9 / 35, 9 / 35, 4 / 35]),
        "service_level_score": rng.uniform(0.75, 0.99, n_dist).round(2),  # ASSUMPTION
    })
    return product, materials, suppliers, distributors


def gen_production(rng, product, n_batches):
    """Batches every few days; one QC test per batch on the same day."""
    first = pd.Timestamp("2023-01-05")
    step = max(1, (END - first).days // max(n_batches - 1, 1))   # ASSUMPTION: regular schedule
    rows = []
    # ASSUMPTION: batch_status is independent of yield (as in the original file)
    status = rng.choice(["Completed", "Delayed", "On Hold"], n_batches, p=[0.615, 0.196, 0.189])
    lines = rng.choice(["Maribor Line A", "Maribor Line B", "Maribor Line C"], n_batches,
                       p=[135 / 465, 157 / 465, 173 / 465])
    target = product.set_index("product_id")["target_yield_rate"]
    for i in range(n_batches):
        date = first + pd.Timedelta(days=step * i)
        pid = rng.choice([p[0] for p in launched(date)])
        planned = int(rng.integers(700, 3188))                   # ASSUMPTION: 700-3,187 litres
        # ASSUMPTION: yield ~ Normal(product target, 0.045), clipped to 75%-99%
        yld = float(np.clip(rng.normal(target[pid], 0.045), 0.75, 0.99))
        actual = int(round(planned * yld))
        cost_per_litre = float(np.clip(rng.normal(0.60, 0.09), 0.40, 0.93))
        rows.append({
            "batch_id": f"BAT{i + 1:05d}", "production_date": date, "product_id": pid,
            "production_line": lines[i], "planned_volume_litre": planned,
            "actual_volume_litre": actual, "production_loss_litre": planned - actual,
            "yield_rate": round(actual / planned, 3),
            "estimated_batch_cost_eur": round(actual * cost_per_litre, 2),
            "shift_count": int(rng.integers(1, 5)), "batch_status": status[i],
        })
    batches = pd.DataFrame(rows)

    abv = product.set_index("product_id")["abv_percent"]
    ph = rng.uniform(4.0, 5.15, n_batches).round(2)                     # ASSUMPTION: pH 4.00-5.15
    measured_abv = (batches["product_id"].map(abv) + rng.uniform(-0.35, 0.35, n_batches)).round(2)   # ASSUMPTION: product ABV +/- 0.35
    abv_dev = (measured_abv - batches["product_id"].map(abv)).abs().round(2)
    # ASSUMPTION (found in Step 7 by feature engineering; the original file follows the same rule for 99.4% of batches):
    # a batch is sent to Review when pH is outside 4.1-5.0 OR the measured ABV is more than 0.30 points from the declared ABV.
    out_of_spec = (ph < 4.1) | (ph > 5.0) | (abv_dev > 0.30)
    qc = pd.DataFrame({
        "qc_test_id": [f"QCT{i + 1:05d}" for i in range(n_batches)],
        "batch_id": batches["batch_id"],
        "test_date": batches["production_date"],
        "temperature_c": rng.uniform(2, 8, n_batches).round(2),
        "ph_value": ph,
        "specific_gravity": rng.uniform(1.008, 1.060, n_batches).round(3),
        "measured_abv_percent": measured_abv,
        "colour_ebc": rng.integers(1, 101, n_batches),
        "defect_units": np.clip(rng.normal(18, 4.5, n_batches).round(), 7, 31).astype(int),
        "quality_status": np.where(out_of_spec, "Review", "Pass"),
    })
    return batches, qc


def gen_procurement(rng, suppliers, materials, n):
    dates = random_dates(rng, n)
    sup_idx = rng.integers(0, len(suppliers), n)
    rows = []
    for i in range(n):
        s = suppliers.iloc[sup_idx[i]]
        # ASSUMPTION: a supplier only delivers materials of its own category
        mats = materials[materials["category"] == s["main_category"]]
        m = mats.iloc[rng.integers(0, len(mats))]
        qty = round(float(rng.uniform(500, 10000)), 2)
        unit_cost = round(m["standard_unit_cost_eur"] * rng.uniform(0.95, 1.12), 3)
        lead = max(2, int(round(rng.normal(s["average_lead_time_days"], 1.5))))
        expected = dates[i] + pd.Timedelta(days=lead)
        # ASSUMPTION: late with probability (1 - supplier's stated on-time rate);
        # a late delivery is 1 + Poisson(2.2) days late, at most 11.
        late = rng.random() > s["on_time_delivery_rate"]
        delay = int(min(1 + rng.poisson(2.2), 11)) if late else 0
        actual = expected + pd.Timedelta(days=delay)
        rows.append({
            "po_id": f"PO{i + 1:05d}", "order_date": dates[i], "supplier_id": s["supplier_id"],
            "material_id": m["material_id"], "quantity_ordered": qty, "unit_cost_eur": unit_cost,
            "purchase_value_eur": round(qty * unit_cost, 2), "expected_delivery_date": expected,
            "actual_delivery_date": actual, "lead_time_days": (actual - dates[i]).days,
            "po_status": "Received" if rng.random() < 0.933 else "Partially Received",
        })
    return pd.DataFrame(rows)


def gen_sales(rng, product, distributors, n_customers, n_orders):
    pinfo = product.set_index("product_id")
    customers = pd.DataFrame({
        "customer_id": [f"CUS{i + 1:04d}" for i in range(n_customers)],
        "customer_alias": [f"Customer_{i + 1:04d}" for i in range(n_customers)],
        "customer_type": rng.choice(["Online Customer", "Hotel", "Bar", "Retailer", "Restaurant"], n_customers),
        "country": rng.choice(COUNTRIES, n_customers),
        "account_size": rng.choice(["Small", "Medium", "Large"], n_customers, p=[0.31, 0.37, 0.32]),
    })

    dates = np.sort(random_dates(rng, n_orders).values)
    # ASSUMPTION: order_status is independent of order date (as in the original file)
    status = rng.choice(["Delivered", "Cancelled", "Open", "Shipped"], n_orders, p=[0.516, 0.17, 0.16, 0.154])
    orders = pd.DataFrame({
        "order_id": [f"ORD{i + 1:06d}" for i in range(n_orders)],
        "order_date": dates,
        "customer_id": rng.choice(customers["customer_id"], n_orders),
        "distributor_id": rng.choice(distributors["distributor_id"], n_orders),
        "sales_channel": rng.choice(["Distributor", "Online", "Hospitality", "Retail"], n_orders),
        "ship_to_country": rng.choice(COUNTRIES, n_orders),
        "order_status": status, "currency": "EUR",
    })

    lines = []
    for _, o in orders.iterrows():
        eligible = [p[0] for p in launched(o["order_date"])]
        k = int(rng.integers(1, 5))                               # ASSUMPTION: 1-4 lines per order
        for j, pid in enumerate(rng.choice(eligible, size=min(k, len(eligible)), replace=False), start=1):
            qty = int(np.clip(round(rng.beta(1.1, 1.6) * 1200), 1, 1200))   # ASSUMPTION: skewed, 1-1,200
            price = round(pinfo.loc[pid, "wholesale_price_eur"] * rng.uniform(0.94, 1.08), 2)
            disc = round(float(rng.uniform(0, 0.18)), 3)          # ASSUMPTION: 0%-18% discount
            net = round(qty * price * (1 - disc), 2)
            cogs = round(qty * pinfo.loc[pid, "unit_variable_cost_eur"], 2)
            lines.append({
                "order_line_id": f"{o['order_id']}-{j}", "order_id": o["order_id"], "product_id": pid,
                "quantity_units": qty, "unit_selling_price_eur": price, "discount_rate": disc,
                "net_sales_eur": net, "estimated_cogs_eur": cogs, "gross_profit_eur": round(net - cogs, 2),
            })
    lines = pd.DataFrame(lines)

    # first_order_date is DERIVED from the orders, so it is always consistent
    first = orders.groupby("customer_id")["order_date"].min()
    customers["first_order_date"] = customers["customer_id"].map(first)
    customers["first_order_date"] = customers["first_order_date"].fillna(
        pd.Series(random_dates(rng, n_customers), index=customers.index))
    customers = customers[["customer_id", "customer_alias", "customer_type", "country",
                           "first_order_date", "account_size"]]
    return customers, orders, lines


def gen_feedback(rng, customers, product, n):
    pick = rng.integers(0, len(FEEDBACK), n)
    return pd.DataFrame({
        "feedback_id": [f"FB{i + 1:05d}" for i in range(n)],
        "feedback_date": random_dates(rng, n),
        "customer_id": rng.choice(customers["customer_id"], n),
        "product_id": rng.choice(product["product_id"], n),
        "feedback_type": rng.choice(["Complaint", "Return Request", "Review"], n, p=[0.294, 0.338, 0.368]),
        "feedback_text": [FEEDBACK[i][0] for i in pick],
        "sentiment_label": [FEEDBACK[i][1] for i in pick],
        "case_status": rng.choice(["Resolved", "Open", "Escalated"], n, p=[0.368, 0.332, 0.30]),
        "issue_category": [FEEDBACK[i][2] for i in pick],
    })


# ---------------------------------------------------------------- self-check
def check(t):
    """Validate the generated data: unique IDs, valid links, correct formulas, same columns."""
    print("\nSELF-CHECK")
    keys = {"Product_Master": "product_id", "Suppliers": "supplier_id", "Distributors": "distributor_id",
            "Customers": "customer_id", "Production_Batches": "batch_id", "Quality_Control": "qc_test_id",
            "Procurement_Orders": "po_id", "Sales_Orders": "order_id", "Sales_Order_Lines": "order_line_id",
            "Customer_Feedback": "feedback_id"}
    fks = [("Sales_Orders", "customer_id", "Customers", "customer_id"),
           ("Sales_Orders", "distributor_id", "Distributors", "distributor_id"),
           ("Sales_Order_Lines", "order_id", "Sales_Orders", "order_id"),
           ("Sales_Order_Lines", "product_id", "Product_Master", "product_id"),
           ("Production_Batches", "product_id", "Product_Master", "product_id"),
           ("Quality_Control", "batch_id", "Production_Batches", "batch_id"),
           ("Procurement_Orders", "supplier_id", "Suppliers", "supplier_id"),
           ("Procurement_Orders", "material_id", "Raw_Materials", "material_id"),
           ("Customer_Feedback", "customer_id", "Customers", "customer_id"),
           ("Customer_Feedback", "product_id", "Product_Master", "product_id")]
    ok = True

    def result(label, passed):
        nonlocal ok
        ok &= passed
        print(f"  [{'OK  ' if passed else 'FAIL'}] {label}")

    for tbl, k in keys.items():
        result(f"{tbl}.{k} unique", t[tbl][k].is_unique)
    for c, cc, p, pc in fks:
        result(f"{c}.{cc} -> {p}.{pc}", t[c][cc].isin(t[p][pc]).all())
    s = t["Sales_Order_Lines"]
    result("net_sales = qty x price x (1 - discount)",
           ((s.quantity_units * s.unit_selling_price_eur * (1 - s.discount_rate) - s.net_sales_eur).abs() < 0.011).all())
    b = t["Production_Batches"]
    result("production_loss = planned - actual", (b.planned_volume_litre - b.actual_volume_litre == b.production_loss_litre).all())
    po = t["Procurement_Orders"]
    result("lead_time = actual_delivery - order_date",
           ((po.actual_delivery_date - po.order_date).dt.days == po.lead_time_days).all())
    m = t["Sales_Orders"].merge(t["Customers"], on="customer_id")
    result("no order before customer's first_order_date", (m.order_date >= m.first_order_date).all())

    if ORIGINAL_FILE.exists():
        orig = pd.read_excel(ORIGINAL_FILE, sheet_name=None)
        same = all(list(t[n].columns) == list(orig[n].columns) for n in t)
        result("column names identical to the original file", same)
        print("\nKPI comparison (synthetic vs original):")
        def kpis(d):
            nc = d["Sales_Orders"].order_status != "Cancelled"
            ln = d["Sales_Order_Lines"].merge(d["Sales_Orders"], on="order_id")
            ln = ln[ln.order_status != "Cancelled"]
            p = d["Procurement_Orders"]
            return {
                "avg yield %": 100 * d["Production_Batches"].yield_rate.mean(),
                "QC review rate %": 100 * (d["Quality_Control"].quality_status == "Review").mean(),
                "cancelled orders %": 100 * (~nc).mean(),
                "gross margin %": 100 * ln.gross_profit_eur.sum() / ln.net_sales_eur.sum(),
                "supplier on-time %": 100 * (pd.to_datetime(p.actual_delivery_date) <= pd.to_datetime(p.expected_delivery_date)).mean(),
                "negative feedback %": 100 * (d["Customer_Feedback"].sentiment_label == "Negative").mean(),
            }
        a, b2 = kpis(t), kpis(orig)
        for k in a:
            print(f"    {k:<22} synthetic {a[k]:6.1f}   original {b2[k]:6.1f}")
    print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Velora synthetic data generator")
    ap.add_argument("--seed", type=int, default=42, help="random seed (same seed = same data)")
    ap.add_argument("--scale", type=float, default=1.0, help="row-count multiplier (1.0 = original size)")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    sc = lambda n: max(10, int(round(n * args.scale)))

    product, materials, suppliers, distributors = gen_reference(rng, args.scale)
    batches, qc = gen_production(rng, product, sc(465))
    procurement = gen_procurement(rng, suppliers, materials, sc(1200))
    customers, orders, lines = gen_sales(rng, product, distributors, sc(600), sc(4500))
    feedback = gen_feedback(rng, customers, product, sc(500))

    tables = {"Product_Master": product, "Raw_Materials": materials, "Suppliers": suppliers,
              "Distributors": distributors, "Customers": customers, "Production_Batches": batches,
              "Quality_Control": qc, "Procurement_Orders": procurement, "Sales_Orders": orders,
              "Sales_Order_Lines": lines, "Customer_Feedback": feedback}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating with seed={args.seed}, scale={args.scale}")
    for name, df in tables.items():
        df = df.copy()
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c] = df[c].dt.strftime("%Y-%m-%d")
        df.to_csv(OUT_DIR / f"{name}.csv", index=False)
        print(f"  {name:<22} {len(df):>6} rows")
    check(tables)
    print(f"\nCSV files saved in {OUT_DIR}/")


if __name__ == "__main__":
    main()
