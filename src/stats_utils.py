"""
stats_utils.py  -  STEP 7a: Small, well-explained statistics helpers (numpy + scipy only).

Plain-English guide
  confidence interval (CI)  a range that very likely contains the true value ("yield is 88.6%, 95% CI 88.1%-89.1%")
  p-value                   how surprising the data would be if there were NO real effect (small = surprising)
  effect size               HOW BIG the difference is (a tiny difference can still have a tiny p-value)
  multiple testing          run 30 tests and about 1-2 will look "significant" by pure luck, so we correct
"""

import numpy as np
import pandas as pd
from scipy import stats


# ------------------------------------------------------------------ confidence intervals
def t_ci(x, level=0.95):
    """CI for a mean (t-interval). Returns (mean, low, high)."""
    x = np.asarray(x, dtype=float)
    m, se = x.mean(), stats.sem(x)
    lo, hi = stats.t.interval(level, len(x) - 1, loc=m, scale=se)
    return m, lo, hi


def wilson_ci(k, n, level=0.95):
    """CI for a proportion (Wilson). Better than the textbook formula for small groups. Returns (p, low, high)."""
    z = stats.norm.ppf(0.5 + level / 2)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, centre - half, centre + half


def bootstrap_ratio_ci(num, den, level=0.95, n_boot=2000, seed=42):
    """CI for sum(num)/sum(den), e.g. gross margin = sum(profit)/sum(sales).
    Resamples the rows with replacement many times. Pass one row per ORDER (not per line) so that
    lines of the same order stay together (they are not independent)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    n = len(num)
    est = num.sum() / den.sum()
    out = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, n, n)
        out[b] = num[i].sum() / den[i].sum()
    lo, hi = np.percentile(out, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return est, lo, hi


def slope_ci(x, y, level=0.95):
    """Straight-line fit y = a + b*x. Returns (slope, low, high, p_value, r)."""
    r = stats.linregress(x, y)
    h = stats.t.ppf(0.5 + level / 2, len(x) - 2) * r.stderr
    return r.slope, r.slope - h, r.slope + h, r.pvalue, r.rvalue


# ------------------------------------------------------------------ effect sizes
def cohens_d(a, b):
    """Difference between two group means in units of their spread (0.2 small, 0.5 medium, 0.8 large)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / sp


def eta_squared(groups):
    """Share of the total variation explained by group membership (0.01 small, 0.06 medium, 0.14 large)."""
    allv = np.concatenate([np.asarray(g, float) for g in groups])
    gm = allv.mean()
    ssb = sum(len(g) * (np.mean(g) - gm) ** 2 for g in groups)
    sst = ((allv - gm) ** 2).sum()
    return ssb / sst


def cramers_v(table):
    """Strength of association between two categories (0 none, 0.1 small, 0.3 medium, 0.5 large)."""
    table = np.asarray(table)
    chi2 = stats.chi2_contingency(table, correction=False)[0]
    return float(np.sqrt(chi2 / (table.sum() * (min(table.shape) - 1))))


def min_detectable_diff(p, n1, n2, alpha=0.05, power=0.8):
    """Smallest difference between two proportions that a test would reliably (80%) detect."""
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return float(z * np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)))


# ------------------------------------------------------------------ multiple testing
def holm_adjust(p):
    """Holm correction: controls the chance of ANY false alarm across all tests."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def bh_adjust(p):
    """Benjamini-Hochberg: controls the SHARE of false alarms among the findings (less strict than Holm)."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)[::-1]
    adj = np.empty(m)
    running = 1.0
    for k, idx in enumerate(order):
        rank = m - k
        running = min(running, p[idx] * m / rank)
        adj[idx] = running
    return adj


# ------------------------------------------------------------------ time series
def trend_with_seasonality(series):
    """Fit  value = a + b*time + month effects  (least squares). Returns (slope per period, low, high, p).
    Month effects stop the strong seasonal swings from hiding a real trend."""
    s = series.dropna()
    n = len(s)
    t = np.arange(n, dtype=float)
    months = pd.get_dummies(s.index.month, drop_first=True).values.astype(float)
    X = np.column_stack([np.ones(n), t, months])
    beta, *_ = np.linalg.lstsq(X, s.values.astype(float), rcond=None)
    resid = s.values - X @ beta
    dof = n - X.shape[1]
    sigma2 = (resid ** 2).sum() / dof
    se = np.sqrt(sigma2 * np.linalg.inv(X.T @ X)[1, 1])
    tstat = beta[1] / se
    p = 2 * stats.t.sf(abs(tstat), dof)
    h = stats.t.ppf(0.975, dof) * se
    return beta[1], beta[1] - h, beta[1] + h, p


def seasonal_profile(series):
    """Detrend a monthly series, then return (seasonal index per calendar month in % of the average month,
    share of the detrended variation explained by the calendar month, ANOVA p, Kruskal p)."""
    s = series.dropna()
    t = np.arange(len(s))
    lr = stats.linregress(t, s.values)
    resid = pd.Series(s.values - (lr.intercept + lr.slope * t), index=s.index)
    groups = [g.values for _, g in resid.groupby(resid.index.month)]
    index = (resid.groupby(resid.index.month).mean() / s.mean() * 100).round(1)
    eta2 = eta_squared(groups)
    return index, eta2, stats.f_oneway(*groups).pvalue, stats.kruskal(*groups).pvalue, resid
