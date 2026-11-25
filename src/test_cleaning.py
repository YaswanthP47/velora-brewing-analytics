"""
test_cleaning.py  -  STEP 6c: Prove the cleaning functions really work.

Run from the project folder:   python src/test_cleaning.py

Idea: our Velora data is already tidy, so we deliberately MAKE A MESS of a copy
(duplicates, blanks, text numbers, bad dates, extra spaces, wrong case, a huge
outlier) and check that the pipeline repairs it. If every check says OK, the
functions are reusable on any other table.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cleaning import CleanLog, convert_types, flag_outliers, handle_missing, remove_duplicates  # noqa: E402
from load_data import load_data_tables  # noqa: E402

PASSED = []


def check(label, condition):
    PASSED.append(bool(condition))
    print(f"  [{'OK  ' if condition else 'FAIL'}] {label}")


def make_dirty(clean):
    """Return a messy copy of Sales_Order_Lines joined with order dates, plus the list of damage done."""
    rng = np.random.default_rng(0)
    d = clean.head(400).copy()
    d["order_date"] = d["order_date"].dt.strftime("%d/%m/%Y")                     # dates as text, day first
    d["net_sales_eur"] = d["net_sales_eur"].map(lambda v: f"EUR {v:,.2f}")        # numbers as text
    d["sales_channel"] = d["sales_channel"].map(lambda v: f"  {v}  ")             # stray spaces
    d.loc[d.index[:25], "sales_channel"] = d.loc[d.index[:25], "sales_channel"].str.upper()  # wrong case
    d["order_id"] = d["order_id"].str.lower()                                      # IDs in lower case
    d.loc[rng.choice(d.index, 30, replace=False), "quantity_units"] = np.nan      # 30 blanks
    d = pd.concat([d, d.sample(20, random_state=1)], ignore_index=True)            # 20 exact duplicate rows
    d.loc[5, "quantity_units"] = 900_000                                           # one absurd value
    return d


def main():
    t = load_data_tables()
    base = t["Sales_Order_Lines"].merge(t["Sales_Orders"][["order_id", "order_date", "sales_channel"]], on="order_id")
    dirty = make_dirty(base)
    print(f"Messy table: {len(dirty)} rows, {dirty['quantity_units'].isna().sum()} blanks, "
          f"{dirty.duplicated().sum()} duplicate rows, dates and amounts stored as text\n")

    log = CleanLog()
    c = convert_types(dirty, "demo", log, dayfirst=True)   # European dates: day/month/year
    c = remove_duplicates(c, "demo", log, key="order_line_id")
    c = handle_missing(c, "demo", log, key="order_line_id", group="sales_channel")   # same-channel median: Online lines are tiny
    c["qty_outlier"] = flag_outliers(c, "quantity_units", group="sales_channel")

    print("Checks:")
    check("order_date is now a real date", pd.api.types.is_datetime64_any_dtype(c["order_date"]))
    original = base.head(400).set_index("order_line_id")["order_date"]
    check("day/month/year dates are read correctly (all 400 match the original dates)",
          (c.drop_duplicates("order_line_id").set_index("order_line_id")["order_date"] == original).all())
    wrong = convert_types(dirty, "demo", CleanLog(), dayfirst=False)
    check("WITHOUT dayfirst=True some dates would be read the wrong way (why the option exists)",
          not (wrong.drop_duplicates("order_line_id").set_index("order_line_id")["order_date"] == original).all())
    check("net_sales_eur is now a number", pd.api.types.is_numeric_dtype(c["net_sales_eur"]))
    check("amounts are correct after removing 'EUR' and commas",
          np.allclose(c.drop_duplicates("order_line_id").set_index("order_line_id")["net_sales_eur"].sort_index().values,
                      base.head(400).set_index("order_line_id")["net_sales_eur"].sort_index().values, atol=0.01))
    check("extra spaces removed from sales_channel", (c["sales_channel"] == c["sales_channel"].str.strip()).all())
    check("UPPER-case channel names unified (4 channels remain)", c["sales_channel"].nunique() == 4)
    check("order_id values are upper case", c["order_id"].str.isupper().all())
    check("the 20 duplicate rows are gone", len(c) == 400)
    check("no blanks left in quantity_units", c["quantity_units"].notna().all())
    check("filled rows are flagged (quantity_units_was_missing)", c["quantity_units_was_missing"].sum() >= 25)
    check("the absurd quantity 900,000 is flagged as an outlier", bool(c["qty_outlier"].iloc[5]))
    check("only a few rows are flagged as outliers (under 2%)", c["qty_outlier"].mean() < 0.02)
    check("real text such as 'Customer_0001' is NOT turned into a number",
          convert_types(pd.DataFrame({"a": [f"Customer_{i:04d}" for i in range(20)]}))["a"].dtype != float)
    print("\nWhat the cleaner did:")
    print(log.frame().to_string(index=False))
    ok = all(PASSED)
    print("\nALL TESTS PASSED" if ok else "\nSOME TESTS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
