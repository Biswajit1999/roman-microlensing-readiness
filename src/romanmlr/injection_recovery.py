"""Synthetic point-lens injection/recovery engine.

The current validated pathway is point-lens only. The repository's custom
binary-lens solver is retained for diagnosis but is deliberately unavailable
to scientific runs until it passes an independent reference-model comparison.

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
from .detect import blind_search_pspl, event_delta_chi2
from .noise import NoiseConfig, add_noise
from .planetary import free_floating_planet_magnification
from .pspl import PSPLParams


@dataclass(frozen=True)
class TrialConfig:
    channel: str  # "planetary" or "ffp"
    u0: float
    tE: float
    rho: float
    t0: float | None = None
    q: float = 0.0     # planetary channel only
    s: float = 1.0     # planetary channel only
    fs: float = 1.0
    fb: float = 0.0
    mag_ref: float = 19.0  # baseline source brightness, mag, sets photon noise
    seed: int = 0
    detection_threshold: float = 500.0
    anomaly_threshold: float = 160.0
    cadence: CadenceConfig = field(default_factory=CadenceConfig)
    noise: NoiseConfig = field(default_factory=NoiseConfig)
    search_timescale_grid_days: tuple[float, ...] = (
        0.02, 0.08, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0,
    )
    grid_n: int = 400  # binary-lens ray-shooting resolution (planetary channel)


@dataclass
class TrialResult:
    config: TrialConfig
    event_detected: bool
    anomaly_detected: bool
    recovered: bool
    parameters_recovered: bool
    event_delta_chi2: float
    anomaly_delta_chi2: float
    failure_reason: str
    n_points_in_anomaly_window: int
    wall_time_s: float
    injected_t0: float
    fitted_t0: float
    fitted_u0: float
    fitted_tE: float
    fit_success: bool
    cadence_seed: int
    epoch_seed: int
    noise_seed: int
    nearest_epoch_minutes: float
    n_epochs_within_tE: int
    season_edge_distance_tE: float


def _sample_event_epoch(cfg: TrialConfig, rng: np.random.Generator) -> float:
    if cfg.t0 is not None:
        return float(cfg.t0)
    season = int(rng.integers(0, len(cfg.cadence.season_start_days)))
    return float(cfg.cadence.season_start_days[season] + rng.uniform(0, cfg.cadence.season_length_days))


def _stream_seeds(master_seed: int) -> tuple[int, int, int]:
    """Derive independent cadence, epoch, and noise streams from one seed."""
    children = np.random.SeedSequence(master_seed).spawn(3)
    return tuple(int(child.generate_state(1, dtype=np.uint32)[0]) for child in children)


def _season_edge_distance_tE(cfg: TrialConfig, t0: float) -> float:
    """Distance from the injected peak to its nearest season edge, in tE."""
    for start in cfg.cadence.season_start_days:
        end = start + cfg.cadence.season_length_days
        if start <= t0 <= end:
            return float(min(t0 - start, end - t0) / cfg.tE)
    return float("nan")


def run_trial(cfg: TrialConfig) -> TrialResult:
    start = time.perf_counter()
    cadence_seed, epoch_seed, noise_seed = _stream_seeds(cfg.seed)
    obs_cadence = CadenceConfig(**{**asdict(cfg.cadence), "seed": cadence_seed})
    t = generate_observation_times(obs_cadence)
    if cfg.channel == "planetary" or cfg.q > 0:
        raise RuntimeError(
            "planetary inference is disabled: the inverse-ray-shooting solver has not "
            "passed independent binary-lens validation"
        )

    rng = np.random.default_rng(epoch_seed)
    injected_t0 = _sample_event_epoch(cfg, rng)
    truth = PSPLParams(t0=injected_t0, u0=cfg.u0, tE=cfg.tE)
    tau = (t - truth.t0) / truth.tE
    beta = np.full_like(tau, truth.u0)

    u = np.sqrt(tau**2 + beta**2)
    amp = free_floating_planet_magnification(u, cfg.rho)

    flux_clean = cfg.fs * amp + cfg.fb
    mag_clean = -2.5 * np.log10(np.clip(flux_clean, 1e-6, None)) + cfg.mag_ref
    noise_cfg = NoiseConfig(**{**asdict(cfg.noise), "seed": noise_seed})
    mag_noisy, sigma_mag = add_noise(mag_clean, noise_cfg)
    flux_noisy = 10 ** (-0.4 * (mag_noisy - cfg.mag_ref))
    sigma_flux = np.abs(flux_noisy * np.log(10) * 0.4 * sigma_mag)
    sigma_flux = np.maximum(sigma_flux, 1e-6)

    fit = blind_search_pspl(
        t,
        flux_noisy,
        sigma_flux,
        timescale_grid_days=cfg.search_timescale_grid_days,
    )

    dchi2_event = event_delta_chi2(fit, flux_noisy, sigma_flux)
    event_detected = fit.success and dchi2_event > cfg.detection_threshold

    epoch_offsets = np.abs(t - truth.t0)
    nearest_epoch_minutes = float(epoch_offsets.min() * 24.0 * 60.0)
    n_epochs_within_tE = int(np.count_nonzero(epoch_offsets <= truth.tE))
    season_edge_distance_tE = _season_edge_distance_tE(cfg, truth.t0)

    if cfg.channel == "ffp":
        # The FFP signal *is* the single-lens event fit here; there is no
        # separate host-star baseline for a perturbation to sit on top of,
        # so a single-lens fit describes the true model and the anomaly
        # window's residual chi2 is expected to be pure noise (~n_points)
        # regardless of event brightness -- it is diagnostic only and does
        # not gate recovery. Recovery is event detection alone.
        anomaly_detected = False
        parameters_recovered = bool(
            event_detected
            and abs(fit.params.t0 - truth.t0) <= max(0.1 * truth.tE, cfg.cadence.cadence_minutes / 1440)
            and abs(fit.params.tE - truth.tE) / truth.tE <= 0.5
            and abs(fit.params.u0 - truth.u0) <= 0.2
        )
        recovered = event_detected
        if recovered:
            reason = "event_detected_parameters_recovered" if parameters_recovered else "event_detected_parameters_not_recovered"
        else:
            reason = "event_below_threshold"
    else:
        raise ValueError("channel must be 'ffp'; planetary inference is disabled")

    elapsed = time.perf_counter() - start
    return TrialResult(
        config=cfg,
        event_detected=bool(event_detected),
        anomaly_detected=bool(anomaly_detected),
        recovered=bool(recovered),
        parameters_recovered=bool(parameters_recovered),
        event_delta_chi2=float(dchi2_event),
        anomaly_delta_chi2=float("nan"),
        failure_reason=reason,
        n_points_in_anomaly_window=0,
        wall_time_s=elapsed,
        injected_t0=injected_t0,
        fitted_t0=float(fit.params.t0),
        fitted_u0=float(fit.params.u0),
        fitted_tE=float(fit.params.tE),
        fit_success=bool(fit.success),
        cadence_seed=cadence_seed,
        epoch_seed=epoch_seed,
        noise_seed=noise_seed,
        nearest_epoch_minutes=nearest_epoch_minutes,
        n_epochs_within_tE=n_epochs_within_tE,
        season_edge_distance_tE=season_edge_distance_tE,
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
            "injected_t0": r.injected_t0,
            "fitted_t0": r.fitted_t0,
            "fitted_u0": r.fitted_u0,
            "fitted_tE": r.fitted_tE,
            "fit_success": r.fit_success,
            "cadence_seed": r.cadence_seed,
            "epoch_seed": r.epoch_seed,
            "noise_seed": r.noise_seed,
            "nearest_epoch_minutes": r.nearest_epoch_minutes,
            "n_epochs_within_tE": r.n_epochs_within_tE,
            "season_edge_distance_tE": r.season_edge_distance_tE,
            "event_delta_chi2": r.event_delta_chi2,
            "anomaly_delta_chi2": r.anomaly_delta_chi2,
            "event_detected": r.event_detected,
            "anomaly_detected": r.anomaly_detected,
            "recovered": r.recovered,
            "parameters_recovered": r.parameters_recovered,
            "failure_reason": r.failure_reason,
            "n_points_in_anomaly_window": r.n_points_in_anomaly_window,
            "wall_time_s": r.wall_time_s,
        }
        rows.append(row)
    return pd.DataFrame(rows)
