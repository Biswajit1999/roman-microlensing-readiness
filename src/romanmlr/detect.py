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


def _fit_pspl_single_attempt(
    t: np.ndarray, flux: np.ndarray, sigma: np.ndarray, x0: list, lower: list, upper: list,
) -> PSPLFitResult | None:
    def resid(theta):
        t0, u0, log_tE, fs, fb = theta
        tE = np.exp(log_tE)
        u = np.sqrt(((t - t0) / tE) ** 2 + u0**2)
        model = flux_model(u, fs, fb)
        return (model - flux) / sigma

    x0_clipped = np.clip(x0, lower, upper)
    try:
        res = least_squares(resid, x0_clipped, method="trf", bounds=(lower, upper), max_nfev=5000)
        t0, u0, log_tE, fs, fb = res.x
        chi2 = float(np.sum(res.fun**2))
        if not np.isfinite(chi2):
            return None
        return PSPLFitResult(
            params=PSPLParams(t0=t0, u0=abs(u0), tE=np.exp(log_tE)),
            fs=fs, fb=fb, chi2=chi2, success=bool(res.success),
        )
    except Exception:  # noqa: BLE001 - any solver failure means "this attempt did not converge"
        return None


def fit_pspl(
    t: np.ndarray,
    flux: np.ndarray,
    sigma: np.ndarray,
    initial_guess: PSPLParams,
    fs0: float = 1.0,
    fb0: float = 0.0,
) -> PSPLFitResult:
    """Nonlinear least-squares single-lens fit (no parallax, no blending prior).

    Multi-start: for high-magnification (small u0) events, a single
    Levenberg-Marquardt-style start from the nominal guess can converge to
    a poor local minimum where u0/tE and fs/fb trade off against each
    other, giving a badly-fit light curve with a very large chi2 despite
    "success" being reported by the optimizer (caught during development
    by actually inspecting fit residuals, not just checking convergence
    flags -- see docs/VALIDATION.md). Several perturbed starting points
    are tried and the lowest-chi2 result is kept, a standard, simple
    robustness technique for exactly this failure mode.
    """
    t = np.asarray(t)
    flux = np.asarray(flux)
    sigma = np.asarray(sigma)

    # Bounded trust-region-reflective fit: without bounds, a Levenberg-
    # Marquardt step can chase a binary-lens/systematic residual the
    # single-lens model cannot fit and drive log_tE to overflow, which
    # silently turns the fit into NaNs rather than a clean failure. The
    # bounds keep tE/u0 in an astrophysically sane range (0.01-10^4 days,
    # 0-20 Einstein radii) and t0 within a wide window of the data span.
    #
    # fs/fb bounds of +-1e3 (an early version of this project) were wide
    # enough to let the optimizer run away to a degenerate, nearly-
    # cancelling (fs, fb) pair (e.g. fs=146, fb=-145) that fits a small
    # subset of points while destroying the fit everywhere else -- caught
    # by inspecting fit parameters directly against injected truth, not
    # by a convergence-flag check alone (the optimizer reports "success"
    # for this degenerate solution too; see docs/VALIDATION.md). Every
    # synthetic light curve in this project is generated with fs=1, fb=0
    # (TrialConfig's defaults, never overridden by any config), so
    # bounding fs/fb to a generously wide but non-degenerate range is a
    # safe, documented restriction for this project's use, not a general
    # single-lens-fitting recommendation for real blended photometry.
    t_span = float(t.max() - t.min()) if t.size else 1.0
    lower = [t.min() - t_span, 0.0, np.log(1e-2), -2.0, -2.0]
    upper = [t.max() + t_span, 20.0, np.log(1e4), 5.0, 5.0]

    u0_guess = max(initial_guess.u0, 1e-3)
    tE_guess = max(initial_guess.tE, 1e-3)
    starts = [
        (initial_guess.t0, u0_guess, np.log(tE_guess), fs0, fb0),
        (initial_guess.t0, u0_guess * 2, np.log(tE_guess), fs0, fb0),
        (initial_guess.t0, u0_guess * 0.5, np.log(tE_guess), fs0, fb0),
        (initial_guess.t0, u0_guess, np.log(tE_guess * 0.7), fs0, fb0),
        # data-driven blending estimate: baseline flux from the faintest
        # 20% of points, peak from the brightest, as an fs/fb starting
        # point independent of the (possibly wrong) fs0/fb0 arguments
        (initial_guess.t0, u0_guess, np.log(tE_guess),
         float(np.percentile(flux, 95) - np.percentile(flux, 20)), float(np.percentile(flux, 20))),
    ]

    best = None
    for x0 in starts:
        result = _fit_pspl_single_attempt(t, flux, sigma, list(x0), lower, upper)
        if result is not None and (best is None or result.chi2 < best.chi2):
            best = result

    if best is None:
        return PSPLFitResult(params=initial_guess, fs=fs0, fb=fb0, chi2=np.inf, success=False)
    return best


def blind_search_pspl(
    t: np.ndarray,
    flux: np.ndarray,
    sigma: np.ndarray,
    timescale_grid_days: tuple[float, ...] = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0),
) -> PSPLFitResult:
    """Search for a PSPL event without access to injected parameters.

    For each predeclared timescale, a boxcar matched-filter supplies a peak
    epoch. Those data-derived candidates seed the same bounded PSPL fitter.
    Null and injected light curves use this identical search and trial space.
    """
    t = np.asarray(t, dtype=float)
    flux = np.asarray(flux, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    if t.size < 5 or flux.shape != t.shape or sigma.shape != t.shape:
        raise ValueError("t, flux, and sigma must be matching arrays with at least five samples")
    if np.any(sigma <= 0) or np.any(~np.isfinite(sigma)):
        raise ValueError("sigma must be finite and positive")
    cadence = float(np.median(np.diff(t)))
    baseline = float(np.median(flux))
    standardized = (flux - baseline) / sigma
    candidates: list[PSPLFitResult] = []
    for tE in timescale_grid_days:
        if tE <= 0:
            raise ValueError("timescale grid values must be positive")
        width = int(np.clip(round(2.0 * tE / max(cadence, 1e-9)), 1, min(t.size, 2001)))
        kernel = np.ones(width) / width
        score = np.convolve(standardized, kernel, mode="same")
        t0_guess = float(t[int(np.argmax(score))])
        guess = PSPLParams(t0=t0_guess, u0=0.3, tE=tE)
        fs0 = max(float(np.percentile(flux, 95) - baseline), 0.1)
        fitted = fit_pspl(t, flux, sigma, guess, fs0=fs0, fb0=baseline - fs0)
        if fitted.success and np.isfinite(fitted.chi2):
            candidates.append(fitted)
    if not candidates:
        fallback = PSPLParams(t0=float(t[np.argmax(flux)]), u0=1.0, tE=1.0)
        return PSPLFitResult(fallback, 1.0, 0.0, np.inf, False)
    return min(candidates, key=lambda result: result.chi2)


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
