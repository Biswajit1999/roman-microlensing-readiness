"""Point-source, point-lens (PSPL) microlensing model, with optional annual/orbital
parallax, following the standard formalism used throughout the literature:

    A(u)  = (u**2 + 2) / (u * sqrt(u**2 + 4))                    [Paczynski 1986]
    u(t)  = sqrt(tau(t)**2 + beta(t)**2)                          [trajectory]

Parallax (Gould 2004, ApJ 606, 319; the "geocentric"-frame projection is applied
here in a Sun-centered frame using the observer ephemeris directly, which is the
convention used by the WFIRST/Roman 2018 Microlensing Data Challenge ephemeris
files):

    tau(t) = (t - t0) / tE + delta_tau(t)
    beta(t) = u0 + delta_beta(t)

    delta_tau(t) =  piEN * dsN(t) + piEE * dsE(t)
    delta_beta(t) = -piEN * dsE(t) + piEE * dsN(t)

    dsN/E(t) = sN/E(t) - sN/E(t0) - (t - t0) * d(sN/E)/dt |_{t0}

where sN(t), sE(t) are the observer's Sun-centered position projected onto the
North/East tangent-plane basis at the target's (RA, Dec), in AU, and piE is the
microlensing parallax vector (piEN, piEE) with |piE| = au / rE (Einstein radius
projected onto the observer plane).

No approximation is used in the point-lens magnification itself: A(u) is exact.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def magnification_pspl(u: np.ndarray) -> np.ndarray:
    """Exact Paczynski (1986) point-lens magnification.

    Parameters
    ----------
    u : array_like
        Lens-source separation in units of the angular Einstein radius.

    Returns
    -------
    A : ndarray
        Magnification, >= 1 for all finite u, -> 1 as u -> inf.
    """
    u = np.asarray(u, dtype=float)
    u2 = u * u
    return (u2 + 2.0) / (u * np.sqrt(u2 + 4.0))


def sky_basis_vectors(ra_deg: float, dec_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (N_hat, E_hat) unit vectors of the tangent plane at (ra, dec).

    Standard equatorial tangent-plane basis (e.g. Gould 2004; matches the
    convention used by pyLIMA and by the WFIRST data-challenge ephemerides,
    which are given in the J2000 equatorial frame).
    """
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    e_hat = np.array([-np.sin(ra), np.cos(ra), 0.0])
    n_hat = np.array([-np.sin(dec) * np.cos(ra), -np.sin(dec) * np.sin(ra), np.cos(dec)])
    return n_hat, e_hat


def parallax_deltas(
    t: np.ndarray,
    t0: float,
    ephem_t: np.ndarray,
    ephem_xyz: np.ndarray,
    ra_deg: float,
    dec_deg: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Project observer ephemeris onto (N, E) and compute Gould (2004) delta_s(t).

    Parameters
    ----------
    t : array_like
        Observation times (same time system as ephem_t and t0), days.
    t0 : float
        Reference time (peak time of the unperturbed trajectory), days.
    ephem_t : array_like
        Ephemeris sample times, days.
    ephem_xyz : array_like, shape (N, 3)
        Sun-centered observer position at ephem_t, AU, equatorial (J2000) frame.
    ra_deg, dec_deg : float
        Target coordinates, degrees.

    Returns
    -------
    ds_n, ds_e : ndarray
        Non-linear (parallax) part of the projected observer displacement, AU,
        interpolated onto ``t``.
    """
    n_hat, e_hat = sky_basis_vectors(ra_deg, dec_deg)
    s_n = ephem_xyz @ n_hat
    s_e = ephem_xyz @ e_hat

    # velocity at t0 via central finite difference on the ephemeris grid
    dt = np.gradient(ephem_t)
    v_n = np.gradient(s_n) / dt
    v_e = np.gradient(s_e) / dt

    s_n_t0 = np.interp(t0, ephem_t, s_n)
    s_e_t0 = np.interp(t0, ephem_t, s_e)
    v_n_t0 = np.interp(t0, ephem_t, v_n)
    v_e_t0 = np.interp(t0, ephem_t, v_e)

    s_n_t = np.interp(t, ephem_t, s_n)
    s_e_t = np.interp(t, ephem_t, s_e)

    ds_n = s_n_t - s_n_t0 - (np.asarray(t) - t0) * v_n_t0
    ds_e = s_e_t - s_e_t0 - (np.asarray(t) - t0) * v_e_t0
    return ds_n, ds_e


@dataclass(frozen=True)
class PSPLParams:
    """Point-lens trajectory parameters."""

    t0: float   # days, time of closest approach (no parallax) or reference epoch
    u0: float   # dimensionless impact parameter
    tE: float   # days, Einstein radius crossing time
    piEN: float = 0.0
    piEE: float = 0.0


def trajectory(
    t: np.ndarray,
    params: PSPLParams,
    ephem: dict | None = None,
    ra_deg: float | None = None,
    dec_deg: float | None = None,
) -> np.ndarray:
    """Compute u(t) for a PSPL trajectory, with optional parallax.

    ``ephem`` must provide {"t": array, "xyz": array (N,3)} when piEN/piEE != 0.
    """
    t = np.asarray(t, dtype=float)
    tau = (t - params.t0) / params.tE
    beta = np.full_like(tau, params.u0)

    if params.piEN != 0.0 or params.piEE != 0.0:
        if ephem is None or ra_deg is None or dec_deg is None:
            raise ValueError("parallax requires ephem, ra_deg, dec_deg")
        ds_n, ds_e = parallax_deltas(t, params.t0, ephem["t"], ephem["xyz"], ra_deg, dec_deg)
        tau = tau + params.piEN * ds_n + params.piEE * ds_e
        beta = beta + (-params.piEN * ds_e + params.piEE * ds_n)

    return np.sqrt(tau**2 + beta**2)


def flux_model(u: np.ndarray, fs: float, fb: float) -> np.ndarray:
    """Blended flux model: F(t) = fs * A(u(t)) + fb."""
    return fs * magnification_pspl(u) + fb
