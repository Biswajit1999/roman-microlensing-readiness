"""Transparent detection statistics: single-lens PSPL fitting and delta-chi2
significance tests.

Two thresholds are used, both standard in the published microlensing
literature (not tuned for this project):

* Event detection: delta_chi2(flat line -> best-fit PSPL) above a threshold
  (default 500, comparable to survey-alert thresholds discussed in Penny
  et al. 2019, ApJS 241, 3).
* Anomaly (planet/FFP-perturbation) detection: delta_chi2 of the residuals
  from the best-fit *single*-lens PSPL model, summed over data points,
  compared against a threshold of 160 -- the widely used value from
  high-magnification planet-search programs (e.g. Gould et al. 2010, ApJ 720,
  1073) and adopted in Roman yield forecasts (Penny et al. 2019).

Both thresholds are exposed as configuration, matching this project's
research question about how selection thresholds change completeness and
false-positive rate.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .pspl import PSPLParams, flux_model


@dataclass
class PSPLFitResult:
    params: PSPLParams
    fs: float
    fb: float
    chi2: float
    success: bool


def fit_pspl(
    t: np.ndarray,
    flux: np.ndarray,
    sigma: np.ndarray,
    initial_guess: PSPLParams,
    fs0: float = 1.0,
    fb0: float = 0.0,
) -> PSPLFitResult:
    """Nonlinear least-squares single-lens fit (no parallax, no blending prior)."""
    t = np.asarray(t)
    flux = np.asarray(flux)
    sigma = np.asarray(sigma)

    def resid(theta):
        t0, u0, log_tE, fs, fb = theta
        tE = np.exp(log_tE)
        u = np.sqrt(((t - t0) / tE) ** 2 + u0**2)
        model = flux_model(u, fs, fb)
        return (model - flux) / sigma

    x0 = [initial_guess.t0, initial_guess.u0, np.log(max(initial_guess.tE, 1e-3)), fs0, fb0]
    # Bounded trust-region-reflective fit: without bounds, a Levenberg-
    # Marquardt step can chase a binary-lens/systematic residual the
    # single-lens model cannot fit and drive log_tE to overflow, which
    # silently turns the fit into NaNs rather than a clean failure. The
    # bounds keep tE/u0 in an astrophysically sane range (0.01-10^4 days,
    # 0-20 Einstein radii) and t0 within a wide window of the data span.
    t_span = float(t.max() - t.min()) if t.size else 1.0
    lower = [t.min() - t_span, 0.0, np.log(1e-2), -1e3, -1e3]
    upper = [t.max() + t_span, 20.0, np.log(1e4), 1e3, 1e3]
    x0_clipped = np.clip(x0, lower, upper)
    try:
        res = least_squares(resid, x0_clipped, method="trf", bounds=(lower, upper), max_nfev=5000)
        t0, u0, log_tE, fs, fb = res.x
        chi2 = float(np.sum(res.fun**2))
        if not np.isfinite(chi2):
            return PSPLFitResult(params=initial_guess, fs=fs0, fb=fb0, chi2=np.inf, success=False)
        return PSPLFitResult(
            params=PSPLParams(t0=t0, u0=abs(u0), tE=np.exp(log_tE)),
            fs=fs,
            fb=fb,
            chi2=chi2,
            success=bool(res.success),
        )
    except Exception:  # noqa: BLE001 - any solver failure means "fit did not converge"
        return PSPLFitResult(params=initial_guess, fs=fs0, fb=fb0, chi2=np.inf, success=False)


def chi2_flat(flux: np.ndarray, sigma: np.ndarray) -> float:
    """Chi2 of the best-fit constant (no lensing) model."""
    weights = 1.0 / sigma**2
    const = np.sum(flux * weights) / np.sum(weights)
    return float(np.sum(((flux - const) / sigma) ** 2))


def event_delta_chi2(fit: PSPLFitResult, flux: np.ndarray, sigma: np.ndarray) -> float:
    return chi2_flat(flux, sigma) - fit.chi2


def anomaly_delta_chi2(
    t: np.ndarray,
    flux: np.ndarray,
    sigma: np.ndarray,
    single_lens_fit: PSPLFitResult,
    anomaly_mask: np.ndarray,
) -> float:
    """Chi2 excess of the single-lens residuals inside ``anomaly_mask``.

    This is the standard "does a single lens explain the anomaly region"
    statistic; a large value means the single-lens model fits poorly there,
    i.e. a planetary/FFP perturbation (or systematic) is present.
    """
    u = np.sqrt(
        ((t - single_lens_fit.params.t0) / single_lens_fit.params.tE) ** 2
        + single_lens_fit.params.u0**2
    )
    model = flux_model(u, single_lens_fit.fs, single_lens_fit.fb)
    resid = (flux - model) / sigma
    return float(np.sum(resid[anomaly_mask] ** 2))
