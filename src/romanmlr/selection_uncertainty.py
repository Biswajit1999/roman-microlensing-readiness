"""Selection-function sensitivity using the committed v0.5 synthetic trials.

These utilities quantify software-experiment sensitivity. They do not convert
the balanced injection grid into a Roman population completeness forecast.
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import binom

from .completeness import wilson_interval


def threshold_operating_curve(
    injections: pd.DataFrame,
    null_trials: pd.DataFrame,
    thresholds: Iterable[float],
) -> pd.DataFrame:
    """Re-evaluate the stored blind-search statistic at fixed thresholds.

    Detection requires a successful fit and a finite ``event_delta_chi2`` above
    threshold. ``balanced_precision`` assumes equal signal/null prior weight and
    is only a software diagnostic, not an astrophysical positive predictive value.
    """
    required = {"event_delta_chi2", "fit_success"}
    for label, table in (("injections", injections), ("null_trials", null_trials)):
        missing = required - set(table.columns)
        if missing:
            raise KeyError(f"{label} missing columns: {sorted(missing)}")
    rows = []
    for threshold in thresholds:
        if not np.isfinite(threshold):
            raise ValueError("thresholds must be finite")
        detected = injections["fit_success"].astype(bool) & (
            pd.to_numeric(injections["event_delta_chi2"], errors="coerce") > threshold
        )
        false_trigger = null_trials["fit_success"].astype(bool) & (
            pd.to_numeric(null_trials["event_delta_chi2"], errors="coerce") > threshold
        )
        signal_k, signal_n = int(detected.sum()), len(injections)
        null_k, null_n = int(false_trigger.sum()), len(null_trials)
        sensitivity, sensitivity_lo, sensitivity_hi = wilson_interval(signal_k, signal_n)
        fpr, fpr_lo, fpr_hi = wilson_interval(null_k, null_n)
        balanced_precision = sensitivity / (sensitivity + fpr) if sensitivity + fpr else np.nan
        rows.append(
            {
                "threshold_delta_chi2": float(threshold),
                "signal_detected": signal_k,
                "signal_trials": signal_n,
                "conditional_detection_fraction": sensitivity,
                "detection_ci_low": sensitivity_lo,
                "detection_ci_high": sensitivity_hi,
                "null_triggers": null_k,
                "null_trials": null_n,
                "simple_null_fpr": fpr,
                "fpr_ci_low": fpr_lo,
                "fpr_ci_high": fpr_hi,
                "balanced_precision": float(balanced_precision),
            }
        )
    return pd.DataFrame(rows).sort_values("threshold_delta_chi2").reset_index(drop=True)


def cadence_dropout_retention(
    injections: pd.DataFrame,
    dropout_fractions: Iterable[float],
    minimum_retained_epochs: int = 3,
) -> pd.DataFrame:
    """Expected probability of retaining minimum near-peak cadence support.

    Each stored epoch within one Einstein time is independently retained with
    probability ``1 - dropout``. This analytic thinning experiment does not
    re-fit light curves and is therefore a cadence-support sensitivity, not a
    revised detection fraction.
    """
    if "n_epochs_within_tE" not in injections:
        raise KeyError("missing n_epochs_within_tE")
    if minimum_retained_epochs < 1:
        raise ValueError("minimum_retained_epochs must be positive")
    counts = pd.to_numeric(injections["n_epochs_within_tE"], errors="raise").to_numpy(int)
    if np.any(counts < 0):
        raise ValueError("epoch counts cannot be negative")
    rows = []
    for dropout in dropout_fractions:
        if not 0 <= dropout < 1:
            raise ValueError("dropout fractions must satisfy 0 <= f < 1")
        retention_probability = binom.sf(minimum_retained_epochs - 1, counts, 1.0 - dropout)
        rows.append(
            {
                "dropout_fraction": float(dropout),
                "minimum_retained_epochs": minimum_retained_epochs,
                "mean_retention_probability": float(np.mean(retention_probability)),
                "events_below_requirement_before_dropout": int(np.sum(counts < minimum_retained_epochs)),
                "n_injections": int(counts.size),
            }
        )
    return pd.DataFrame(rows)


def minimum_trials_for_wilson_precision(
    target_half_width: float,
    assumed_fraction: float = 0.5,
    max_trials: int = 1_000_000,
) -> int:
    """Smallest binomial sample with Wilson half-width at most the target."""
    if not 0 < target_half_width < 0.5 or not 0 <= assumed_fraction <= 1:
        raise ValueError("invalid target width or assumed fraction")
    for n in range(1, max_trials + 1):
        k = round(assumed_fraction * n)
        _, low, high = wilson_interval(k, n)
        if (high - low) / 2 <= target_half_width:
            return n
    raise ValueError("precision target not reached within max_trials")


def injection_count_plan(
    target_half_widths: Iterable[float] = (0.10, 0.05, 0.03, 0.02),
    assumed_fractions: Iterable[float] = (0.1, 0.5, 0.9),
) -> pd.DataFrame:
    """Plan per-bin injection counts without claiming observational power."""
    rows = []
    for fraction in assumed_fractions:
        for width in target_half_widths:
            rows.append(
                {
                    "assumed_recovery_fraction": float(fraction),
                    "target_wilson_half_width": float(width),
                    "minimum_trials_per_bin": minimum_trials_for_wilson_precision(width, fraction),
                }
            )
    return pd.DataFrame(rows)
