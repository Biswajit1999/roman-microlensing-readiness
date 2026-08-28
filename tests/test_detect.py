import numpy as np

from romanmlr.detect import anomaly_delta_chi2, event_delta_chi2, fit_pspl
from romanmlr.pspl import PSPLParams, flux_model, trajectory


def _make_light_curve(seed=0, n=400, u0=0.05, tE=25.0, t0=0.0, fs=1.0, fb=0.0, sigma=0.01):
    rng = np.random.default_rng(seed)
    t = np.linspace(-100, 100, n)
    truth = PSPLParams(t0=t0, u0=u0, tE=tE)
    u = trajectory(t, truth)
    clean = flux_model(u, fs, fb)
    noisy = clean + rng.normal(0, sigma, n)
    return t, noisy, np.full(n, sigma), truth


def test_fit_recovers_injected_parameters():
    t, flux, sigma, truth = _make_light_curve(seed=1)
    guess = PSPLParams(t0=truth.t0 + 2, u0=truth.u0 * 1.5, tE=truth.tE * 0.8)
    fit = fit_pspl(t, flux, sigma, guess)
    assert fit.success
    assert abs(fit.params.t0 - truth.t0) < 1.0
    assert abs(fit.params.tE - truth.tE) / truth.tE < 0.1
    assert abs(fit.params.u0 - truth.u0) < 0.02


def test_event_detected_well_above_threshold():
    t, flux, sigma, truth = _make_light_curve(seed=2, u0=0.05)
    fit = fit_pspl(t, flux, sigma, truth)
    dchi2 = event_delta_chi2(fit, flux, sigma)
    assert dchi2 > 500  # clear high-SNR event


def test_pure_noise_does_not_trigger_detection():
    rng = np.random.default_rng(3)
    t = np.linspace(-100, 100, 400)
    sigma = np.full(400, 0.01)
    flux = 1.0 + rng.normal(0, 0.01, 400)
    guess = PSPLParams(t0=0.0, u0=0.5, tE=20.0)
    fit = fit_pspl(t, flux, sigma, guess)
    dchi2 = event_delta_chi2(fit, flux, sigma)
    assert dchi2 < 500


def test_anomaly_chi2_flags_injected_deviation():
    t, flux, sigma, truth = _make_light_curve(seed=4)
    fit = fit_pspl(t, flux, sigma, truth)
    anomaly_mask = np.zeros(t.size, dtype=bool)
    anomaly_mask[195:205] = True
    flux_with_bump = flux.copy()
    flux_with_bump[anomaly_mask] += 0.5  # inject an obvious localized deviation
    dchi2_anomaly = anomaly_delta_chi2(t, flux_with_bump, sigma, fit, anomaly_mask)
    dchi2_baseline = anomaly_delta_chi2(t, flux, sigma, fit, anomaly_mask)
    assert dchi2_anomaly > 160
    assert dchi2_baseline < 160
