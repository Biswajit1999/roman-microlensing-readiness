"""Photometric noise model: photon/read noise plus an optional correlated
(red-noise) systematic component.

White (photon+read) noise is modeled as Gaussian with a magnitude-dependent
sigma from a simple two-term model (Roman-like: dominant Poisson term plus a
floor from residual systematics/read noise), calibrated to be of order the
per-point scatter seen in the public WFIRST 2018 Microlensing Data Challenge
light curves (see docs/DATA_SOURCES.md) rather than a from-scratch instrument
ETC. Correlated noise is added as a stationary AR(1) (Ornstein-Uhlenbeck-like)
process, which is the simplest transparent model of time-correlated
systematics (e.g. residual flat-fielding or thermal drift); it is a
documented simplification, not a full instrument-systematics model
(see docs/LIMITATIONS.md).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NoiseConfig:
    sigma_floor_mag: float = 0.003
    sigma_poisson_mag_at_ref: float = 0.01
    mag_ref: float = 21.0
    # Photon-limited relative uncertainty scales as flux**-1/2, hence
    # 10**(0.2 * delta_mag). This remains a phenomenological noise proxy.
    poisson_index: float = 0.2
    rho_ar1: float = 0.0  # AR(1) correlation coefficient per epoch; 0 = white noise
    red_noise_amp_mag: float = 0.0  # stddev of the AR(1) component
    seed: int = 0


def photometric_sigma(mag: np.ndarray, cfg: NoiseConfig) -> np.ndarray:
    """Magnitude-dependent per-point uncertainty (mag), fainter -> noisier."""
    mag = np.asarray(mag, dtype=float)
    sigma_poisson = cfg.sigma_poisson_mag_at_ref * 10 ** (cfg.poisson_index * (mag - cfg.mag_ref))
    return np.sqrt(cfg.sigma_floor_mag**2 + sigma_poisson**2)


def _ar1_series(n: int, rho: float, amp: float, rng: np.random.Generator) -> np.ndarray:
    if amp <= 0 or n == 0:
        return np.zeros(n)
    innovations = rng.normal(0.0, amp * np.sqrt(max(1.0 - rho**2, 1e-6)), size=n)
    series = np.empty(n)
    series[0] = rng.normal(0.0, amp)
    for i in range(1, n):
        series[i] = rho * series[i - 1] + innovations[i]
    return series


def add_noise(mag_clean: np.ndarray, cfg: NoiseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Add white + AR(1) correlated noise to a clean magnitude series.

    Returns (mag_noisy, sigma).
    """
    rng = np.random.default_rng(cfg.seed)
    mag_clean = np.asarray(mag_clean, dtype=float)
    sigma = photometric_sigma(mag_clean, cfg)
    white = rng.normal(0.0, sigma)
    red = _ar1_series(mag_clean.size, cfg.rho_ar1, cfg.red_noise_amp_mag, rng)
    return mag_clean + white + red, sigma
