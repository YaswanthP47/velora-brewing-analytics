"""
preprocess.py  -  STEP 6b: Encoding and scaling for machine learning (scikit-learn).

Machine-learning models need numbers only, on similar scales:
    ENCODING  turns words into 0/1 columns        ('Lager' -> style_Lager = 1)
    SCALING   puts numbers on one scale (mean 0)  (so litres do not outweigh pH)
    IMPUTING  fills any blank before the model sees it

GOLDEN RULE (avoids "data leakage"): learn the medians, means and categories
from the TRAINING rows only, then apply them to the test rows. For time data we
split by DATE (train = past, test = future), never randomly.

Kept separate from cleaning.py so the cleaning still works even if
scikit-learn cannot be loaded on a computer.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TRAIN_END = pd.Timestamp("2025-12-31")   # train on 2023-2025, test on 2026

# ready-made problems used in Steps 7 and 8
QC_PROBLEM = {
    "table": "batches_qc", "target": "is_review", "date_col": "production_date",
    "numeric": ["planned_volume_litre", "yield_rate", "shift_count", "temperature_c", "ph_value",
                "specific_gravity", "measured_abv_percent", "colour_ebc", "defect_units", "month_no"],
    "categorical": ["product_name", "production_line", "batch_status"],
}
DEMAND_PROBLEM = {
    "table": "demand", "target": "units_sold", "date_col": "month",
    "numeric": ["promotion_discount_rate", "month_no", "year"],
    "categorical": ["product_id", "season"],
    "exclude": "is_forecast_period",        # months after 2026-10-31 are not real history
}


def build_preprocessor(numeric, categorical):
    """Numbers: fill blanks with the median, then scale. Words: fill with the most common, then one-hot encode."""
    num = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("num", num, numeric), ("cat", cat, categorical)], verbose_feature_names_out=False)


def prepare(tables, problem, train_end=TRAIN_END):
    """Split by date, fit the preprocessor on TRAIN only, transform both parts."""
    df = tables[problem["table"]].copy()
    if problem.get("exclude"):
        df = df[~df[problem["exclude"]]]
    train, test = df[df[problem["date_col"]] <= train_end], df[df[problem["date_col"]] > train_end]
    cols = problem["numeric"] + problem["categorical"]
    pre = build_preprocessor(problem["numeric"], problem["categorical"])
    X_train = pd.DataFrame(pre.fit_transform(train[cols]), columns=pre.get_feature_names_out(), index=train.index)
    X_test = pd.DataFrame(pre.transform(test[cols]), columns=pre.get_feature_names_out(), index=test.index)
    return {"X_train": X_train, "X_test": X_test, "y_train": train[problem["target"]], "y_test": test[problem["target"]],
            "preprocessor": pre, "feature_names": list(X_train.columns)}
