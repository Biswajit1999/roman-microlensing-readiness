"""Linear-limb-darkened finite-source point-lens microlensing diagnostics.

The linear law is I(mu) = I(1) [1 - c(1-mu)], 0 <= c <= 1,
mu = sqrt(1 - (r/rho)^2). Its disk-average intensity is I(1)(1-c/3).
Numerical quadrature deliberately makes no claims about binary lenses.
"""
from __future__ import annotations

import numpy as np


def _point_lens(separation: np.ndarray) -> np.ndarray:
    """Exact point-lens amplification (Paczynski 1986)."""
    u = np.asarray(separation, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (u * u + 2) / (u * np.sqrt(u * u + 4))


def linear_source_magnification(
    separation: np.ndarray,
    rho: float,
    coefficient: float,
    *,
    n_radial: int = 48,
    n_angular: int = 128,
) -> np.ndarray:
    """Integrate a linearly limb-darkened source disk against point-lens A(u).

    Parameters are dimensionless. `separation` may be scalar or ndarray.
    The integral is normalized by the *unlensed* disk flux; no spurious
    amplitude change is introduced when the limb coefficient changes.
    The lens singularity is integrable but may require quadrature convergence
    checks when u ~ rho. This is a slow, transparent reference calculation.
    """
    if not (np.isfinite(rho) and rho > 0):
        raise ValueError("rho must be finite and positive")
    if not (np.isfinite(coefficient) and 0 <= coefficient <= 1):
        raise ValueError("linear limb-darkening coefficient must lie in [0, 1]")
    if n_radial < 8 or n_angular < 16:
        raise ValueError("quadrature requires at least 8 radial and 16 angular nodes")
    u = np.asarray(separation, dtype=float)
    if not np.all(np.isfinite(u)) or np.any(u < 0):
        raise ValueError("lens-source separation must be finite and nonnegative")
    # Integrate in lens-centred polar coordinates rather than source-centred
    # coordinates. The integrable A(s) ~ 1/s singularity is removed by the
    # polar-area Jacobian s, avoiding arbitrary epsilon clipping near u=rho.
    radial_nodes, radial_weights = np.polynomial.legendre.leggauss(n_radial)
    angular_nodes, angular_weights = np.polynomial.legendre.leggauss(n_angular)
    out = np.empty_like(u, dtype=float)
    normalization = np.pi * rho * rho * (1 - coefficient / 3)
    for index in np.ndindex(u.shape):
        offset = float(u[index])
        # Split at the transition from full-circle to partial-circle arcs.
        boundaries = ([0.0, rho - offset, rho + offset] if offset < rho
                      else [offset - rho, offset + rho])
        flux = 0.0
        for low, high in zip(boundaries[:-1], boundaries[1:]):
            if high <= low:
                continue
            s = 0.5 * (high - low) * (radial_nodes + 1) + low
            ds_weights = 0.5 * (high - low) * radial_weights
            if offset == 0 or (offset < rho and high <= rho - offset):
                phi_max = np.full_like(s, np.pi)
            else:
                q = (s*s + offset*offset - rho*rho) / (2*s*offset)
                phi_max = np.arccos(np.clip(q, -1, 1))
            phi = phi_max[:, None] * angular_nodes[None, :]
            distance2 = s[:, None]**2 + offset**2 - 2*s[:, None]*offset*np.cos(phi)
            mu = np.sqrt(np.maximum(0.0, 1 - distance2 / (rho*rho)))
            intensity = 1 - coefficient * (1 - mu)
            angle_integral = phi_max * (intensity @ angular_weights)
            # Algebraically evaluate s*A(s) without a 0/0 at the origin.
            s_times_amplification = (s*s + 2) / np.sqrt(s*s + 4)
            flux += np.sum(ds_weights * s_times_amplification * angle_integral)
        out[index] = flux / normalization
    return out


def exposure_averaged_magnification(
    time: np.ndarray,
    *,
    t0: float,
    t_e: float,
    u0: float,
    rho: float,
    coefficient: float,
    exposure_days: float,
    n_time: int = 5,
    n_radial: int = 32,
    n_angular: int = 96,
) -> np.ndarray:
    """Average a rectilinear microlensing trajectory over finite exposures.

    Each exposure is a centered top-hat in time, integrated by Gauss-Legendre
    quadrature. This is an instrumental-smearing sensitivity test, not a Roman
    cadence or detector model.
    """
    if not (np.isfinite(t_e) and t_e > 0 and np.isfinite(u0) and u0 >= 0):
        raise ValueError("t_e must be positive and u0 nonnegative")
    if not (np.isfinite(exposure_days) and exposure_days >= 0):
        raise ValueError("exposure_days must be finite and nonnegative")
    if n_time < 1:
        raise ValueError("n_time must be >= 1")
    t = np.asarray(time, dtype=float)
    if not np.all(np.isfinite(t)):
        raise ValueError("time must be finite")
    nodes, weights = np.polynomial.legendre.leggauss(n_time)
    if exposure_days == 0:
        nodes, weights = np.array([0.0]), np.array([2.0])
    result = np.zeros_like(t, dtype=float)
    for node, weight in zip(nodes, weights):
        shifted = t + 0.5 * exposure_days * node
        u = np.hypot((shifted - t0) / t_e, u0)
        result += 0.5 * weight * linear_source_magnification(
            u, rho, coefficient, n_radial=n_radial, n_angular=n_angular
        )
    return result


def quadrature_convergence(
    separation: np.ndarray, rho: float, coefficient: float,
    *, orders: tuple[int, ...] = (24, 48, 96), angular_multiplier: int = 4,
) -> dict[str, np.ndarray]:
    """Compare successively refined disk integrals; difference is not an error bound."""
    if len(orders) < 2 or any(o < 8 for o in orders) or any(b <= a for a, b in zip(orders, orders[1:])):
        raise ValueError("orders must be strictly increasing with >=2 entries")
    if angular_multiplier < 2:
        raise ValueError("angular_multiplier must be >= 2")
    vals = np.stack([
        linear_source_magnification(separation, rho, coefficient,
                                    n_radial=o, n_angular=o * angular_multiplier)
        for o in orders
    ])
    return {"orders": np.asarray(orders), "magnification": vals,
            "relative_change": np.abs(np.diff(vals, axis=0)) / np.maximum(np.abs(vals[1:]), 1e-15)}
