import pytest

from romanmlr.cadence import CadenceConfig
from romanmlr.injection_recovery import TrialConfig, run_grid, run_trial

_FAST_CADENCE = CadenceConfig(
    n_seasons=2, season_length_days=72, season_gap_days=61,
    cadence_minutes=15, downlink_gap_every_hours=12, random_dropout_frac=0.02,
)


def test_bright_high_snr_ffp_event_is_recovered():
    cfg = TrialConfig(
        channel="ffp", u0=0.05, tE=1.5, rho=0.01, t0=40.0,
        mag_ref=17.0, seed=0, cadence=_FAST_CADENCE,
    )
    result = run_trial(cfg)
    assert result.event_detected
    assert result.anomaly_detected
    assert result.failure_reason == "recovered"


def test_faint_shallow_event_is_not_recovered():
    cfg = TrialConfig(
        channel="ffp", u0=1.5, tE=0.3, rho=0.01, t0=40.0,
        mag_ref=24.5, seed=0, cadence=_FAST_CADENCE,
    )
    result = run_trial(cfg)
    assert not (result.event_detected and result.anomaly_detected)


def test_null_trial_no_signal_rarely_triggers_detection():
    # tE effectively infinite / u0 huge => negligible magnification => a
    # pure-noise-like null test of the false-positive machinery.
    false_positives = 0
    n = 15
    for seed in range(n):
        cfg = TrialConfig(
            channel="ffp", u0=50.0, tE=20.0, rho=0.01, t0=40.0,
            mag_ref=21.0, seed=seed, cadence=_FAST_CADENCE,
        )
        r = run_trial(cfg)
        false_positives += int(r.event_detected)
    assert false_positives / n < 0.3  # loose sanity bound, not a tuned FPR claim


@pytest.mark.slow
def test_planetary_channel_runs_end_to_end():
    cfg = TrialConfig(
        channel="planetary", u0=0.05, tE=20.0, rho=0.005, q=0.01, s=1.0, t0=40.0,
        mag_ref=18.0, seed=0, cadence=_FAST_CADENCE, grid_n=300,
    )
    result = run_trial(cfg)
    assert result.event_delta_chi2 >= 0
    assert result.anomaly_delta_chi2 >= 0


def test_run_grid_returns_one_row_per_config():
    configs = [
        TrialConfig(channel="ffp", u0=u0, tE=2.0, rho=0.01, t0=40.0, mag_ref=19.0,
                    seed=0, cadence=_FAST_CADENCE)
        for u0 in (0.05, 0.5, 1.5)
    ]
    df = run_grid(configs)
    assert len(df) == 3
    assert set(df.columns) >= {"u0", "recovered", "event_delta_chi2", "failure_reason"}
