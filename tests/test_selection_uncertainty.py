import pandas as pd
import pytest

from romanmlr.selection_uncertainty import (
    cadence_dropout_retention,
    injection_count_plan,
    minimum_trials_for_wilson_precision,
    threshold_operating_curve,
)


def test_threshold_curve_is_monotonic_and_separates_nulls():
    injections = pd.DataFrame(
        {"fit_success": [True] * 4, "event_delta_chi2": [5, 20, 200, 2000]}
    )
    nulls = pd.DataFrame(
        {"fit_success": [True] * 4, "event_delta_chi2": [1, 2, 10, 30]}
    )
    curve = threshold_operating_curve(injections, nulls, (0, 15, 100, 1000))
    assert curve["conditional_detection_fraction"].is_monotonic_decreasing
    assert curve["simple_null_fpr"].is_monotonic_decreasing
    assert curve.iloc[-1]["null_triggers"] == 0


def test_dropout_retention_matches_binomial_limits():
    trials = pd.DataFrame({"n_epochs_within_tE": [2, 3, 10]})
    result = cadence_dropout_retention(trials, (0.0, 0.5), minimum_retained_epochs=3)
    assert result.iloc[0]["mean_retention_probability"] == pytest.approx(2 / 3)
    assert result.iloc[1]["mean_retention_probability"] < result.iloc[0]["mean_retention_probability"]


def test_precision_plan_requires_more_trials_for_narrower_intervals():
    wide = minimum_trials_for_wilson_precision(0.10, assumed_fraction=0.5)
    narrow = minimum_trials_for_wilson_precision(0.03, assumed_fraction=0.5)
    assert narrow > wide
    assert wide > 20


def test_half_recovery_is_conservative_for_injection_planning():
    plan = injection_count_plan((0.05,), (0.1, 0.5, 0.9)).set_index(
        "assumed_recovery_fraction"
    )
    assert plan.loc[0.5, "minimum_trials_per_bin"] >= plan.loc[0.1, "minimum_trials_per_bin"]
    assert plan.loc[0.5, "minimum_trials_per_bin"] >= plan.loc[0.9, "minimum_trials_per_bin"]
