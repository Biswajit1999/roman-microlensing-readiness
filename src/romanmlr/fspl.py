"""Finite-source point-lens (FSPL) magnification for a uniform-brightness disk
source, computed by direct numerical disk integration of the exact PSPL
magnification rather than a transcribed closed-form elliptic-integral solution.

Analytic closed-form finite-source solutions exist (Gould 1994, ApJ 421, L71;
Witt & Mao 1994, ApJ 430, 505; Yoo et al. 2004, ApJ 603, 139) but require
complete elliptic integrals whose sign/argument conventions are easy to
mis-transcribe -- exactly the kind of silent equation error this project's
research standard requires guarding against. Numerical disk integration of the
already-validated exact point-lens formula is slower but has no closed-form
transcription risk, and it converges to the analytic point-lens magnification
in the rho -> 0 limit, which is used here as the correctness check
(see tests/test_fspl.py and docs/VALIDATION.md).

Finite-source corrections matter only near u ~ rho; the model therefore uses
the numerically integrated disk magnification only within
``fs_threshold * rho`` of the lens and the exact point-lens formula elsewhere,
where the two agree to within the disk-integration quadrature tolerance.
"""
from __future__ import annotations

import numpy as np

from .pspl import magnification_pspl

# Fixed Gauss-Legendre radial quadrature (accurate to <1e-4 relative error for
# uniform-brightness disks at all tested rho, u; see tests/test_fspl.py).
_N_RADIAL = 24
_N_ANGULAR = 48
_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(_N_RADIAL)
_PHI = np.linspace(0.0, 2 * np.pi, _N_ANGULAR, endpoint=False)
_COS_PHI = np.cos(_PHI)
_SIN_PHI = np.sin(_PHI)


def _disk_average_magnification(u: float, rho: float) -> float:
    """(1/(pi rho^2)) * integral over the source disk of A_PSPL, uniform disk."""
    # map Gauss-Legendre nodes on [-1,1] to r in [0, rho]
    r = 0.5 * rho * (_GL_NODES + 1.0)
    w_r = 0.5 * rho * _GL_WEIGHTS  # quadrature weights for the r-integral

    # separation of each grid point from the lens: law of cosines with the
    # disk center placed at distance u along phi=0 (magnification depends
    # only on separation, so orientation of the disk center is arbitrary).
    rr, pp_cos = np.meshgrid(r, _COS_PHI, indexing="ij")
    _, pp_sin = np.meshgrid(r, _SIN_PHI, indexing="ij")
    sep2 = (u + rr * pp_cos) ** 2 + (rr * pp_sin) ** 2
    sep = np.sqrt(np.maximum(sep2, 1e-12))

    a_grid = magnification_pspl(sep)
    # integral over phi (uniform grid, periodic -> plain average is exact
    # to spectral accuracy) then weighted radial sum, including the r
    # Jacobian factor from polar-area element dA = r dr dphi
    phi_avg = a_grid.mean(axis=1) * (2 * np.pi)
    integral = np.sum(w_r * r * phi_avg)
    return integral / (np.pi * rho**2)


def magnification_fspl(
    u: np.ndarray, rho: float, fs_threshold: float = 4.0
) -> np.ndarray:
    """Finite-source magnification for a uniform-brightness disk of radius rho.

    Parameters
    ----------
    u : array_like
        Point-source lens-source separation (Einstein radii).
    rho : float
        Angular source radius in units of the angular Einstein radius,
        rho = thetaS / thetaE. Must be > 0.
    fs_threshold : float
        Apply the disk-integrated correction only for u < fs_threshold * rho;
        elsewhere the exact point-lens formula is used (the two agree to
        within quadrature tolerance well before this radius).
    """
    if rho <= 0:
        raise ValueError("rho must be > 0; use magnification_pspl for rho -> 0")
    u = np.asarray(u, dtype=float)
    near = u < fs_threshold * rho
    with np.errstate(divide="ignore", invalid="ignore"):
        # points inside `near` are overwritten by the disk integral below;
        # the point-lens value computed for them here (possibly inf at u=0)
        # is discarded, so the divide-by-zero warning is suppressed rather
        # than surfaced as a spurious diagnostic.
        out = magnification_pspl(u)
    idx = np.flatnonzero(near)
    for i in idx:
        out[i] = _disk_average_magnification(float(u[i]), rho)
    return out
