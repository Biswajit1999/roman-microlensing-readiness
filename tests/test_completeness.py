import pandas as pd
import pytest

from romanmlr.completeness import completeness_by_bin, false_positive_rate, wilson_interval


def test_wilson_interval_known_values():
    # k=0/n: point estimate 0, interval must not go negative
    p, lo, hi = wilson_interval(0, 20)
    assert p == 0.0
    assert lo == 0.0
    assert hi > 0.0

    # k=n: point estimate 1, interval must not exceed 1
    p, lo, hi = wilson_interval(20, 20)
    assert p == 1.0
    assert hi == 1.0
    assert lo < 1.0

    # k=n/2: symmetric interval around 0.5
    p, lo, hi = wilson_interval(50, 100)
    assert p == pytest.approx(0.5)
    assert (0.5 - lo) == pytest.approx(hi - 0.5, rel=1e-6)


def test_wilson_interval_narrows_with_more_trials():
    _, lo_small, hi_small = wilson_interval(5, 10)
    _, lo_big, hi_big = wilson_interval(500, 1000)
    assert (hi_big - lo_big) < (hi_small - lo_small)


def test_completeness_by_bin_groups_correctly():
    df = pd.DataFrame(
        {
            "u0_bin": [0, 0, 0, 1, 1, 1, 1],
            "recovered": [True, True, False, False, False, False, True],
        }
    )
    out = completeness_by_bin(df, ["u0_bin"])
    out = out.set_index("u0_bin")
    assert out.loc[0, "n_trials"] == 3
    assert out.loc[0, "n_success"] == 2
    assert out.loc[0, "completeness"] == pytest.approx(2 / 3)
    assert out.loc[1, "n_trials"] == 4
    assert out.loc[1, "n_success"] == 1


def test_false_positive_rate_from_null_trials():
    df = pd.DataFrame({"event_detected": [False] * 95 + [True] * 5})
    result = false_positive_rate(df)
    assert result["n_trials"] == 100
    assert result["n_false_positive"] == 5
    assert result["fpr"] == pytest.approx(0.05)
    assert result["ci_low"] < 0.05 < result["ci_high"]
