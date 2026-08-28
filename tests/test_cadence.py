import numpy as np

from romanmlr.cadence import CadenceConfig, generate_observation_times


def test_observation_times_are_sorted_and_within_baseline():
    cfg = CadenceConfig(n_seasons=3, season_length_days=10, season_gap_days=5,
                         cadence_minutes=60, random_dropout_frac=0.0,
                         downlink_gap_every_hours=1e9)
    t = generate_observation_times(cfg)
    assert np.all(np.diff(t) > 0)
    assert t.min() >= 0
    assert t.max() <= cfg.total_baseline_days()


def test_season_gaps_are_respected():
    cfg = CadenceConfig(n_seasons=2, season_length_days=10, season_gap_days=20,
                         cadence_minutes=60, random_dropout_frac=0.0,
                         downlink_gap_every_hours=1e9)
    t = generate_observation_times(cfg)
    gaps = np.diff(t)
    # the single inter-season gap must be much larger than the cadence
    assert gaps.max() > 15  # days, close to the 20-day season_gap_days


def test_dropout_reduces_point_count():
    kwargs = {"n_seasons": 2, "season_length_days": 10, "season_gap_days": 5,
              "cadence_minutes": 30, "downlink_gap_every_hours": 1e9}
    t_full = generate_observation_times(CadenceConfig(random_dropout_frac=0.0, seed=1, **kwargs))
    t_dropout = generate_observation_times(CadenceConfig(random_dropout_frac=0.3, seed=1, **kwargs))
    assert t_dropout.size < t_full.size


def test_deterministic_given_seed():
    cfg = CadenceConfig(seed=42)
    t1 = generate_observation_times(cfg)
    t2 = generate_observation_times(cfg)
    np.testing.assert_array_equal(t1, t2)
