"""
statistics_analysis.py  -  STEP 7b: Statistical quality and profitability analysis.

run_all(clean) returns:
    cis    one row per confidence interval (estimate, low, high)
    tests  one row per hypothesis test (p-value, effect size, p corrected for multiple testing, verdict)
    extra  pieces the notebook draws (control chart numbers, seasonal profile, ...)

How to read the 'verdict' column
    Significant           still significant after Holm correction for ALL tests  -> trust it
    Nominal only          p < 0.05 on its own, but NOT after correction          -> could be luck
    Not significant       no evidence of a difference
Always read the effect size too: significant does not mean important.
"""

import numpy as np
import pandas as pd
from scipy import stats

import stats_utils as su


class Registry:
    """Collects tests and CIs as tidy rows."""

    def __init__(self):
        self.tests, self.cis = [], []

    def test(self, area, question, method, p, effect_name, effect, n, note=""):
        self.tests.append({"area": area, "question": question, "method": method, "n": int(n),
                           "p_value": float(p), "effect_name": effect_name, "effect": float(effect), "note": note})

    def ci(self, area, quantity, est, lo, hi, method, n, unit=""):
        self.cis.append({"area": area, "quantity": quantity, "estimate": float(est), "low": float(lo),
                         "high": float(hi), "method": method, "n": int(n), "unit": unit})

    def finish(self):
        tests = pd.DataFrame(self.tests)
        tests["p_holm"] = su.holm_adjust(tests["p_value"])
        tests["p_bh"] = su.bh_adjust(tests["p_value"])
        tests["verdict"] = np.where(tests["p_holm"] < 0.05, "Significant",
                                    np.where(tests["p_value"] < 0.05, "Nominal only", "Not significant"))
        tests.insert(0, "id", [f"T{i + 1:02d}" for i in range(len(tests))])
        return tests, pd.DataFrame(self.cis)


def anova(groups):
    f = stats.f_oneway(*groups)
    return f.pvalue, su.eta_squared(groups)


def run_all(clean):
    R = Registry()
    b, po, o = clean["batches_qc"], clean["procurement"], clean["Sales_Orders"]
    sl = clean["sales_lines"]
    ok = sl[~sl["is_cancelled"]].copy()
    ok["line_margin"] = ok["gross_profit_eur"] / ok["net_sales_eur"]
    ok["ym"] = ok["order_date"].dt.to_period("M")
    dem = clean["demand"][~clean["demand"]["is_forecast_period"]].copy()
    extra = {}

    # ================= QUALITY: yield =================
    y = b["yield_rate"] * 100
    R.ci("Quality", "Average batch yield", *su.t_ci(y), "t-interval", len(y), "%")
    for line, g in b.groupby("production_line"):
        R.ci("Quality", f"Average yield, {line}", *su.t_ci(g["yield_rate"] * 100), "t-interval", len(g), "%")
    R.ci("Quality", "Average yield minus product target", *su.t_ci(b["yield_gap"] * 100), "t-interval", len(b), "points")

    p, e = anova([g["yield_rate"].values for _, g in b.groupby("production_line")])
    R.test("Quality", "Does yield differ between production lines?", "ANOVA", p, "eta-squared", e, len(b))
    p, e = anova([g["yield_rate"].values for _, g in b.groupby("batch_status")])
    R.test("Quality", "Does yield differ by batch status (Completed / Delayed / On Hold)?", "ANOVA", p, "eta-squared", e, len(b))
    p, e = anova([g["yield_rate"].values for _, g in b.groupby("product_name")])
    R.test("Quality", "Does yield differ between products?", "ANOVA", p, "eta-squared", e, len(b),
           "Expected: each product has its own yield target")
    tt = stats.ttest_1samp(b["yield_gap"], 0)
    R.test("Quality", "Is the average yield different from the product targets?", "one-sample t-test", tt.pvalue,
           "Cohen's d", b["yield_gap"].mean() / b["yield_gap"].std(ddof=1), len(b))
    rho = stats.spearmanr(np.arange(len(b)), b["yield_rate"])
    R.test("Quality", "Is yield drifting up or down over time?", "Spearman correlation with batch order", rho.pvalue,
           "rho", rho.statistic, len(b))

    # control chart (individuals chart, sigma from moving ranges)
    ys = b.sort_values("production_date")["yield_rate"].reset_index(drop=True) * 100
    centre, sigma = ys.mean(), ys.diff().abs().mean() / 1.128
    extra["control"] = {"series": ys, "centre": centre, "ucl": centre + 3 * sigma, "lcl": centre - 3 * sigma,
                        "outside": int(((ys > centre + 3 * sigma) | (ys < centre - 3 * sigma)).sum()),
                        "lag1_autocorr": float(ys.autocorr(1))}

    # ================= QUALITY: review rate =================
    k, n = int(b["is_review"].sum()), len(b)
    R.ci("Quality", "Batch review rate", *[v * 100 for v in su.wilson_ci(k, n)], "Wilson", n, "%")
    for line, g in b.groupby("production_line"):
        R.ci("Quality", f"Review rate, {line}", *[v * 100 for v in su.wilson_ci(int(g["is_review"].sum()), len(g))], "Wilson", len(g), "%")
    for col, label in [("product_name", "product"), ("production_line", "production line")]:
        ct = pd.crosstab(b[col], b["is_review"])
        R.test("Quality", f"Does the review rate differ by {label}?", "chi-square", stats.chi2_contingency(ct)[1],
               "Cramer's V", su.cramers_v(ct), n)
    extra["min_detectable_review_diff"] = su.min_detectable_diff(k / n, int(b.groupby("product_name").size().median()), n)

    meas = [("temperature_c", "temperature"), ("ph_value", "pH"), ("specific_gravity", "specific gravity"),
            ("measured_abv_percent", "measured ABV"), ("colour_ebc", "colour"), ("defect_units", "defect units")]
    for col, label in meas:
        a, r = b.loc[~b["is_review"], col], b.loc[b["is_review"], col]
        R.test("Quality", f"Is {label} different in Review batches?", "Welch t-test", stats.ttest_ind(a, r, equal_var=False).pvalue,
               "Cohen's d (Review - Pass)", su.cohens_d(r, a), n,
               f"Mann-Whitney p = {stats.mannwhitneyu(a, r).pvalue:.3f}")

    # --- the engineered quantity that matters: distance from the DECLARED ABV (direction cancels out in raw averages)
    abv = clean["Product_Master"].set_index("product_id")["abv_percent"]
    gap = (b["measured_abv_percent"] - b["product_id"].map(abv)).abs().round(2)
    a, r = gap[~b["is_review"]], gap[b["is_review"]]
    R.test("Quality", "Is the ABV gap from the declared ABV larger in Review batches?", "Welch t-test", stats.ttest_ind(a, r, equal_var=False).pvalue,
           "Cohen's d (Review - Pass)", su.cohens_d(r, a), n, f"Mann-Whitney p = {stats.mannwhitneyu(a, r).pvalue:.1e}")
    oos = (gap > 0.30) | (b["ph_value"] < 4.1) | (b["ph_value"] > 5.0)
    extra["spec_rule"] = {"accuracy": float((oos == b["is_review"]).mean()), "flagged": int(oos.sum()), "review": int(b["is_review"].sum()),
                          "missed": int((~oos & b["is_review"]).sum()), "false_alarms": int((oos & ~b["is_review"]).sum())}
    bs = b.sort_values(["production_date", "batch_id"])
    prev = bs.groupby("production_line")["is_review"].shift(1)
    m = prev.notna()
    ct = pd.crosstab(prev[m].astype(bool), bs.loc[m, "is_review"])
    R.test("Quality", "Is a batch more likely to be Review if the previous batch on its line was Review?", "chi-square", stats.chi2_contingency(ct)[1],
           "Cramer's V", su.cramers_v(ct), int(m.sum()))

    # ================= SUPPLY =================
    kl = int(po["is_late"].sum())
    R.ci("Supply", "Share of late deliveries", *[v * 100 for v in su.wilson_ci(kl, len(po))], "Wilson", len(po), "%")
    for yr, g in po.groupby(po["order_date"].dt.year):
        R.ci("Supply", f"Share of late deliveries, {yr}", *[v * 100 for v in su.wilson_ci(int(g["is_late"].sum()), len(g))], "Wilson", len(g), "%")
    ct = pd.crosstab(po["supplier_id"], po["is_late"])
    R.test("Supply", "Does the late-delivery share differ between suppliers?", "chi-square", stats.chi2_contingency(ct)[1],
           "Cramer's V", su.cramers_v(ct), len(po))
    ct = pd.crosstab(po["order_date"].dt.year == 2023, po["is_late"])
    R.test("Supply", "Were deliveries later in 2023 than afterwards?", "chi-square (2023 vs 2024-26)", stats.chi2_contingency(ct)[1],
           "Cramer's V", su.cramers_v(ct), len(po))
    sup = clean["Suppliers"]
    rho = stats.spearmanr(sup["on_time_rate_stated"], sup["on_time_rate_calc"])
    R.test("Supply", "Does a supplier's STATED on-time rate predict its real one?", "Spearman correlation", rho.pvalue, "rho", rho.statistic, len(sup))
    R.test("Supply", "Does delay differ by material category?", "Kruskal-Wallis",
           stats.kruskal(*[g["delay_days"].values for _, g in po.groupby("material_category")]).pvalue,
           "eta-squared", su.eta_squared([g["delay_days"].values for _, g in po.groupby("material_category")]), len(po))

    # ================= PROFITABILITY =================
    og = ok.groupby("order_id")[["gross_profit_eur", "net_sales_eur"]].sum()
    R.ci("Profit", "Gross margin (all products)", *[v * 100 for v in su.bootstrap_ratio_ci(og["gross_profit_eur"], og["net_sales_eur"])],
         "bootstrap over orders", len(og), "%")
    prod = []
    for name, g in ok.groupby("product_name"):
        est, lo, hi = [v * 100 for v in su.bootstrap_ratio_ci(g["gross_profit_eur"], g["net_sales_eur"], n_boot=1000)]
        R.ci("Profit", f"Gross margin, {name}", est, lo, hi, "bootstrap over lines", len(g), "%")
        prod.append((name, est / 100))
    pm = clean["Product_Master"].set_index("product_name")["wholesale_price_eur"]
    pr = pd.DataFrame(prod, columns=["product_name", "margin"]).set_index("product_name")
    pr["price"] = pm
    sl_, lo, hi, p, r = su.slope_ci(pr["price"], pr["margin"] * 100)
    R.ci("Profit", "Margin gain per +1 EUR wholesale price", sl_, lo, hi, "regression over 13 products", len(pr), "points")
    R.test("Profit", "Does margin rise with price (13 products)?", "linear regression", p, "r", r, len(pr), f"R-squared = {r * r:.2f}")
    extra["price_fit"] = pr

    sl2, lo2, hi2, p2, r2 = su.slope_ci(ok["discount_rate"] * 100, ok["line_margin"] * 100)
    R.ci("Profit", "Margin change per +1 point of discount", sl2, lo2, hi2, "regression over lines", len(ok), "points")
    R.test("Profit", "Does a bigger discount lower the margin?", "linear regression", p2, "r", r2, len(ok),
           "Partly arithmetic: a discount cuts revenue while cost stays")
    non = ok[ok["sales_channel"] != "Online"]
    sl3, lo3, hi3, p3, r3 = su.slope_ci(non["discount_rate"] * 100, non["quantity_units"])
    R.ci("Profit", "Units per line change per +1 point of discount (non-Online)", sl3, lo3, hi3, "regression over lines", len(non), "units")
    R.test("Profit", "Does a bigger discount bring bigger orders (non-Online)?", "linear regression", p3, "r", r3, len(non))
    p, e = anova([g["line_margin"].values for _, g in ok.groupby("sales_channel")])
    R.test("Profit", "Does the margin differ by sales channel?", "ANOVA", p, "eta-squared", e, len(ok))

    # ================= SALES =================
    monthly = ok.groupby("ym")["net_sales_eur"].sum()
    monthly.index = monthly.index.to_timestamp()
    jo = monthly[monthly.index.month <= 10]
    for yr, g in jo.groupby(jo.index.year):
        R.ci("Sales", f"Average monthly net sales Jan-Oct {yr}", *[v / 1000 for v in su.t_ci(g.values)], "t-interval over months", len(g), "EUR thousand")
    p, e = anova([g.values for _, g in jo.groupby(jo.index.year)])
    R.test("Sales", "Do Jan-Oct monthly sales differ between years?", "ANOVA", p, "eta-squared", e, len(jo))
    rho = stats.spearmanr(np.arange(len(monthly)), monthly.values)
    R.test("Sales", "Is monthly sales trending up or down (46 months)?", "Spearman correlation with time", rho.pvalue, "rho", rho.statistic, len(monthly))
    gm = [g.values for _, g in monthly.groupby(monthly.index.month)]
    R.test("Sales", "Do sales differ by calendar month (seasonality)?", "Kruskal-Wallis", stats.kruskal(*gm).pvalue, "eta-squared", su.eta_squared(gm), len(monthly),
           f"ANOVA p = {stats.f_oneway(*gm).pvalue:.3f}")
    k = int(o["is_cancelled"].sum())
    R.ci("Sales", "Share of cancelled orders", *[v * 100 for v in su.wilson_ci(k, len(o))], "Wilson", len(o), "%")
    for col, label in [("sales_channel", "channel"), ("year", "year")]:
        ct = pd.crosstab(o[col], o["is_cancelled"])
        R.test("Sales", f"Does the cancellation rate differ by {label}?", "chi-square", stats.chi2_contingency(ct)[1], "Cramer's V", su.cramers_v(ct), len(o))
    extra["monthly_sales"] = monthly

    # ================= DEMAND & SEASONALITY =================
    tot = dem.groupby("month")["units_sold"].sum()
    index, eta2, p_a, p_k, resid = su.seasonal_profile(tot)
    R.test("Demand", "Does total demand differ by calendar month (after removing the trend)?", "Kruskal-Wallis", p_k, "eta-squared", eta2, len(tot),
           f"ANOVA p = {p_a:.1e}")
    slope, lo, hi, p = su.trend_with_seasonality(tot)
    R.ci("Demand", "Demand trend per month (seasonally adjusted)", slope, lo, hi, "regression with month effects", len(tot), "units / month")
    R.test("Demand", "Is total demand trending up (seasonally adjusted)?", "regression with month effects", p, "units per month", slope, len(tot))
    extra["naive_trend_p"] = float(stats.linregress(np.arange(len(tot)), tot.values).pvalue)   # trend test WITHOUT month effects
    sig = 0
    for _, g in dem.groupby("product_id"):
        s = g.set_index("month")["units_sold"]
        lr = stats.linregress(np.arange(len(s)), s.values)
        r_ = pd.Series(s.values - (lr.intercept + lr.slope * np.arange(len(s))), index=s.index)
        sig += stats.kruskal(*[q.values for _, q in r_.groupby(r_.index.month)]).pvalue < 0.05
    rho_p = stats.spearmanr(dem["month"].dt.month.map(index), dem["units_sold"])
    R.test("Demand", "Does the total-demand seasonal pattern show up in individual product-months?", "Spearman correlation", rho_p.pvalue, "rho", rho_p.statistic, len(dem),
           "Index fitted on all months, so descriptive only")
    rho = stats.spearmanr(dem["promotion_discount_rate"], dem["units_sold"])
    R.test("Demand", "Do promotions raise units sold?", "Spearman correlation", rho.pvalue, "rho", rho.statistic, len(dem))
    pv = dem.pivot_table(index="month", columns="product_id", values="units_sold")
    extra.update({"seasonal_index": index, "seasonal_eta2": eta2, "total_demand": tot, "detrended": resid,
                  "products_with_seasonality": int(sig), "n_products": dem["product_id"].nunique(),
                  "avg_product_corr": float(pv.corr().values[np.triu_indices(pv.shape[1], 1)].mean())})

    # ================= OTHER =================
    mt = clean["Equipment_Maintenance"]
    p, e = anova([g["downtime_hours"].values for _, g in mt.groupby("maintenance_type")])
    R.test("Other", "Does downtime differ by maintenance type?", "ANOVA", p, "eta-squared", e, len(mt))
    fb = clean["Customer_Feedback"]
    ct = pd.crosstab(fb["feedback_type"], fb["is_negative"])
    R.test("Other", "Does the share of negative feedback differ by feedback type?", "chi-square", stats.chi2_contingency(ct)[1], "Cramer's V", su.cramers_v(ct), len(fb))

    tests, cis = R.finish()
    return cis, tests, extra
