"""Completeness and false-positive-rate surfaces with Wilson-score confidence
intervals (Wilson 1927, JASA 22, 209), the standard interval for small-n
binomial proportions (unlike the normal/Wald interval, it stays inside
[0, 1] and has correct coverage near p=0 or p=1, both of which occur often
in low-completeness or high-completeness bins here).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def wilson_interval(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    """Return (point_estimate, lower, upper) for a binomial proportion.

    ``z`` defaults to the two-sided 95% normal quantile.
    """
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return p, max(0.0, center - half), min(1.0, center + half)


def completeness_by_bin(
    results: pd.DataFrame,
    bin_cols: list[str],
    success_col: str = "recovered",
) -> pd.DataFrame:
    """Group trials by ``bin_cols`` and compute completeness + Wilson CI.

    Every bin also reports ``n_trials`` so downstream users can see (and
    exclude) bins with too few trials for the interval to be meaningful.
    """
    rows = []
    for keys, group in results.groupby(bin_cols):
        keys = keys if isinstance(keys, tuple) else (keys,)
        n = len(group)
        k = int(group[success_col].sum())
        p, lo, hi = wilson_interval(k, n)
        row = dict(zip(bin_cols, keys))
        row.update({"n_trials": n, "n_success": k, "completeness": p, "ci_low": lo, "ci_high": hi})
        rows.append(row)
    return pd.DataFrame(rows)


def false_positive_rate(null_results: pd.DataFrame, detected_col: str = "event_detected") -> dict:
    """False-positive rate from trials with NO injected signal (pure noise
    realizations of the survey cadence/noise model), with a Wilson CI.
    """
    n = len(null_results)
    k = int(null_results[detected_col].sum())
    p, lo, hi = wilson_interval(k, n)
    return {"n_trials": n, "n_false_positive": k, "fpr": p, "ci_low": lo, "ci_high": hi}
