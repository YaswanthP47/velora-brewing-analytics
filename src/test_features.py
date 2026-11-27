"""
test_features.py  -  STEP 7e: Prove the features contain no information from the future.

Run from the project folder:   python src/test_features.py

Two kinds of check:
  1. CORRECTNESS  a lag feature really equals the earlier value; totals add up.
  2. LEAKAGE      we CHANGE the future on purpose and confirm that features for earlier rows do not move.
                  If a feature moves when only the future changed, it was peeking.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cleaning import clean_all  # noqa: E402
from features import TRAIN_END, build_all, demand_features, qc_features  # noqa: E402
from load_data import load_data_tables  # noqa: E402

RESULTS = []


def check(label, condition):
    RESULTS.append(bool(condition))
    print(f"  [{'OK  ' if condition else 'FAIL'}] {label}")


def same(a, b):
    """Two columns equal, treating NaN == NaN."""
    return bool(((a == b) | (a.isna() & b.isna())).all())


def main():
    clean, *_ = clean_all(load_data_tables())
    F = build_all(clean)
    d, q, cust = F["demand_features"], F["qc_features"], F["customer_features"]

    print("1. Correctness")
    d = d.sort_values(["product_id", "month"]).reset_index(drop=True)
    manual_lag1 = d.groupby("product_id")["units_sold"].shift(1)
    check("units_lag1 equals last month's units for every product", same(d["units_lag1"], manual_lag1))
    manual_lag12 = d.groupby("product_id")["units_sold"].shift(12)
    check("units_lag12 equals the same month last year", same(d["units_lag12"], manual_lag12))
    manual_roll = d.groupby("product_id")["units_sold"].transform(lambda s: s.shift(1).rolling(3).mean())
    check("units_roll_mean_3 is the mean of the 3 PREVIOUS months (current month excluded)", np.allclose(d["units_roll_mean_3"].fillna(-1), manual_roll.fillna(-1)))
    check("first month of every product has no lag (nothing is back-filled)", d.groupby("product_id")["units_lag1"].apply(lambda s: s.iloc[0]).isna().all())
    check("the forecast-period months (after 2026-10-31) are not in the demand features", d["month"].max() <= pd.Timestamp("2026-10-31"))
    check("month_sin / month_cos stay between -1 and 1", d[["month_sin", "month_cos"]].abs().max().max() <= 1)
    so = clean["sales_lines"]
    check("customer monetary values add up to total net sales (cancelled excluded)",
          np.isclose(cust["monetary"].sum(), so.loc[~so["is_cancelled"], "net_sales_eur"].sum()))
    check("customer frequency adds up to the non-cancelled orders", int(cust["frequency"].sum()) == int((~clean["Sales_Orders"]["is_cancelled"]).sum()))
    check("recency_days is never negative", (cust["recency_days"].dropna() >= 0).all())
    check("no infinite values in any feature table", all(not np.isinf(v.select_dtypes("number")).any().any() for v in F.values()))

    print("\n2. Leakage (change the future, earlier features must not move)")
    tampered = {k: v.copy() for k, v in clean.items()}
    tampered["demand"] = tampered["demand"].copy()
    future = tampered["demand"]["month"] > TRAIN_END
    tampered["demand"].loc[future, "units_sold"] = 10_000_000          # absurd future values
    d2 = demand_features(tampered).sort_values(["product_id", "month"]).reset_index(drop=True)
    early = d["month"] <= TRAIN_END
    check("seasonal_index does not change when the TEST years are altered (learned from training years only)",
          same(d.loc[early, "seasonal_index"], d2.loc[early, "seasonal_index"]) and same(d["seasonal_index"], d2["seasonal_index"]))
    lag_cols = [c for c in d.columns if c.startswith(("units_lag", "units_roll"))] + ["total_units_lag1"]
    check("lag and rolling features for training rows are unchanged when future units are altered",
          all(same(d.loc[early, c], d2.loc[early, c]) for c in lag_cols))
    first_future = d.loc[d["month"] == pd.Timestamp("2026-01-01"), "units_lag1"].reset_index(drop=True)
    first_future2 = d2.loc[d2["month"] == pd.Timestamp("2026-01-01"), "units_lag1"].reset_index(drop=True)
    check("Jan 2026 lag1 (Dec 2025 units, still known) is unchanged", same(first_future, first_future2))

    tq = {k: v.copy() for k, v in clean.items()}
    b = tq["batches_qc"]
    last = b["production_date"] >= b["production_date"].quantile(0.8)   # change the outcome of the last 20% of batches
    b.loc[last, "is_review"] = ~b.loc[last, "is_review"]
    q2 = qc_features(tq)
    first80 = q["production_date"] < b["production_date"].quantile(0.8)
    check("review_rate_prev10_line of earlier batches does not move when LATER outcomes change",
          same(q.loc[first80, "review_rate_prev10_line"], q2.loc[first80, "review_rate_prev10_line"]))
    check("prev_batch_review_line of earlier batches does not move when LATER outcomes change",
          same(q.loc[first80, "prev_batch_review_line"], q2.loc[first80, "prev_batch_review_line"]))
    check("the first batch on each line has no 'previous batch' feature (nothing is back-filled)",
          q.sort_values("production_date").groupby("production_line")["prev_batch_review_line"].apply(lambda s: s.iloc[0]).isna().all())

    ok = all(RESULTS)
    print("\nALL FEATURE TESTS PASSED" if ok else "\nSOME FEATURE TESTS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
