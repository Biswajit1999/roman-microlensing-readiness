"""Injection-recovery engine: inject a planetary or free-floating-planet (FFP)
signal into a synthetic Roman-GBTDS-like light curve and test whether the
transparent single-lens detection statistic (detect.py) recovers it.

Each trial is fully specified by a frozen, hashable config (seed included),
so every result row is independently reproducible from its own parameters --
no trial depends on execution order or external state.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .cadence import CadenceConfig, generate_observation_times
from .detect import anomaly_delta_chi2, event_delta_chi2, fit_pspl
from .noise import NoiseConfig, add_noise
from .planetary import (
    BinaryLensConfig,
    free_floating_planet_magnification,
    magnification_binary_track,
)
from .pspl import PSPLParams


@dataclass(frozen=True)
class TrialConfig:
    channel: str  # "planetary" or "ffp"
    u0: float
    tE: float
    rho: float
    t0: float = 0.0
    q: float = 0.0     # planetary channel only
    s: float = 1.0     # planetary channel only
    fs: float = 1.0
    fb: float = 0.0
    mag_ref: float = 19.0  # baseline source brightness, mag, sets photon noise
    seed: int = 0
    detection_threshold: float = 500.0
    anomaly_threshold: float = 160.0
    cadence: CadenceConfig = field(default_factory=CadenceConfig)
    grid_n: int = 400  # binary-lens ray-shooting resolution (planetary channel)


@dataclass
class TrialResult:
    config: TrialConfig
    event_detected: bool
    anomaly_detected: bool
    recovered: bool
    event_delta_chi2: float
    anomaly_delta_chi2: float
    failure_reason: str
    n_points_in_anomaly_window: int
    wall_time_s: float


def _anomaly_window_mask(t: np.ndarray, t0: float, tE: float, rho: float, q: float, s: float) -> np.ndarray:
    """Heuristic window around the perturbation used for the anomaly chi2
    statistic: for the FFP channel this is simply the peak region (the whole
    event *is* the anomaly relative to a flat baseline); for the planetary
    channel it is a window around where the source trajectory passes closest
    to the companion at separation s (Einstein radii of the total system).
    """
    if q <= 0:
        return np.abs(t - t0) < 2 * tE
    # time at which |tau| ~ s (closest approach to the companion's location)
    t_anom = t0 + s * tE
    half_width = max(3 * rho * tE, 0.5)
    return np.abs(t - t_anom) < half_width


def run_trial(cfg: TrialConfig) -> TrialResult:
    start = time.perf_counter()
    obs_cadence = CadenceConfig(**{**asdict(cfg.cadence), "seed": cfg.seed})
    t = generate_observation_times(obs_cadence)

    truth = PSPLParams(t0=cfg.t0, u0=cfg.u0, tE=cfg.tE)
    tau = (t - truth.t0) / truth.tE
    beta = np.full_like(tau, truth.u0)

    if cfg.channel == "planetary" and cfg.q > 0:
        blens_cfg = BinaryLensConfig(q=cfg.q, s=cfg.s, rho=cfg.rho, grid_n=cfg.grid_n)
        amp = magnification_binary_track(tau, beta, blens_cfg)
    else:
        u = np.sqrt(tau**2 + beta**2)
        amp = free_floating_planet_magnification(u, cfg.rho)

    flux_clean = cfg.fs * amp + cfg.fb
    mag_clean = -2.5 * np.log10(np.clip(flux_clean, 1e-6, None)) + cfg.mag_ref
    noise_cfg = NoiseConfig(seed=cfg.seed)
    mag_noisy, sigma_mag = add_noise(mag_clean, noise_cfg)
    flux_noisy = 10 ** (-0.4 * (mag_noisy - cfg.mag_ref))
    sigma_flux = np.abs(flux_noisy * np.log(10) * 0.4 * sigma_mag)
    sigma_flux = np.maximum(sigma_flux, 1e-6)

    guess = PSPLParams(t0=cfg.t0, u0=max(cfg.u0, 1e-3), tE=cfg.tE)
    fit = fit_pspl(t, flux_noisy, sigma_flux, guess, fs0=cfg.fs, fb0=cfg.fb)

    dchi2_event = event_delta_chi2(fit, flux_noisy, sigma_flux)
    event_detected = dchi2_event > cfg.detection_threshold

    anomaly_mask = _anomaly_window_mask(t, cfg.t0, cfg.tE, cfg.rho, cfg.q, cfg.s)
    n_anom = int(anomaly_mask.sum())
    dchi2_anom = (
        anomaly_delta_chi2(t, flux_noisy, sigma_flux, fit, anomaly_mask) if n_anom else 0.0
    )

    is_ffp = cfg.channel == "ffp" or cfg.q <= 0
    if is_ffp:
        # The FFP signal *is* the single-lens event fit here; there is no
        # separate host-star baseline for a perturbation to sit on top of,
        # so a single-lens fit describes the true model and the anomaly
        # window's residual chi2 is expected to be pure noise (~n_points)
        # regardless of event brightness -- it is diagnostic only and does
        # not gate recovery. Recovery is event detection alone.
        anomaly_detected = event_detected
        recovered = event_detected
        if recovered:
            reason = "recovered"
        elif n_anom == 0:
            reason = "no_epochs_in_anomaly_window"
        else:
            reason = "event_below_threshold"
    else:
        # Bound-planet channel: the injected data include a genuine
        # binary-lens perturbation that the single-lens fit cannot match,
        # so real excess chi2 in the anomaly window is the detection
        # signature on top of (required) event detection.
        if n_anom == 0:
            anomaly_detected = False
            reason = "no_epochs_in_anomaly_window"
        else:
            anomaly_detected = dchi2_anom > cfg.anomaly_threshold
            if not event_detected:
                reason = "event_below_threshold"
            elif not anomaly_detected:
                reason = "anomaly_below_threshold"
            else:
                reason = "recovered"
        recovered = event_detected and anomaly_detected

    elapsed = time.perf_counter() - start
    return TrialResult(
        config=cfg,
        event_detected=bool(event_detected),
        anomaly_detected=bool(anomaly_detected),
        recovered=bool(recovered),
        event_delta_chi2=float(dchi2_event),
        anomaly_delta_chi2=float(dchi2_anom),
        failure_reason=reason,
        n_points_in_anomaly_window=n_anom,
        wall_time_s=elapsed,
    )


def run_grid(configs: list[TrialConfig]) -> pd.DataFrame:
    """Run every trial config and return one row per trial (flat DataFrame)."""
    rows = []
    for cfg in configs:
        r = run_trial(cfg)
        row = {
            "channel": cfg.channel,
            "u0": cfg.u0,
            "tE": cfg.tE,
            "rho": cfg.rho,
            "q": cfg.q,
            "s": cfg.s,
            "mag_ref": cfg.mag_ref,
            "seed": cfg.seed,
            "event_delta_chi2": r.event_delta_chi2,
            "anomaly_delta_chi2": r.anomaly_delta_chi2,
            "event_detected": r.event_detected,
            "anomaly_detected": r.anomaly_detected,
            "recovered": r.recovered,
            "failure_reason": r.failure_reason,
            "n_points_in_anomaly_window": r.n_points_in_anomaly_window,
            "wall_time_s": r.wall_time_s,
        }
        rows.append(row)
    return pd.DataFrame(rows)
