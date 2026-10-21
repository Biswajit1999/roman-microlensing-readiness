"""Independent point-lens quadrature and binary ray-shooting diagnostics.

Coordinates and radii are in total-mass Einstein-radius units. These
functions diagnose the existing binary solver; they do not validate its
planetary completeness predictions or replace independent solver comparison.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def finite_source_point_lens(u, rho: float, n_phi: int = 192):
    """Uniform-disk PSPL via *analytic radial* and Gauss-Legendre angular integral.

    A(r)*r has primitive F(r) = r*sqrt(r^2+4)/2. For a source disk
    centered at distance u from the lens, integrate F(r_high)-F(r_low)
    over the lens-centered angles that intersect the disk. The source is
    uniformly bright; no limb darkening or binary caustics are included.
    """
    if not np.isfinite(rho) or rho <= 0 or n_phi < 16:
        raise ValueError("rho must be positive and n_phi >= 16")
    values = np.atleast_1d(np.asarray(u, dtype=float))
    if np.any(~np.isfinite(values)) or np.any(values < 0):
        raise ValueError("u must be finite and nonnegative")
    nodes, weights = np.polynomial.legendre.leggauss(n_phi)
    result = np.empty_like(values)
    for i, distance in enumerate(values):
        extent = np.pi if distance <= rho else np.arcsin(rho / distance)
        phi = extent * nodes
        discriminant = np.maximum(rho**2 - distance**2 * np.sin(phi) ** 2, 0.0)
        upper = distance * np.cos(phi) + np.sqrt(discriminant)
        lower = np.maximum(distance * np.cos(phi) - np.sqrt(discriminant), 0.0)
        primitive = lambda r: 0.5 * r * np.sqrt(r**2 + 4)
        integral = extent * np.dot(weights, primitive(upper) - primitive(lower))
        result[i] = integral / (np.pi * rho**2)
    return result.reshape(np.shape(u))


def ray_shot_magnification(tau, beta, *, q: float, s: float, rho: float,
                           grid_n: int, half_width: float, phase: float = 0.5):
    """Fixed-area inverse ray shooting, exposing sub-pixel grid phase.

    Unlike the existing production solver, this diagnostic uses cell-center
    coordinates (phase=.5) and the exact cell area (2*half_width/grid_n)^2.
    No zero-count PSPL floor is applied; zero counts remain visible as a
    failure diagnostic rather than being mistaken for physical zero flux.
    """
    if not (0 <= q < 1 and s > 0 and rho > 0 and half_width > 0
            and 0 <= phase <= 1 and grid_n >= 16):
        raise ValueError("invalid lens or grid parameters")
    step = 2 * half_width / grid_n
    if step > rho:
        raise ValueError("image-plane grid spacing exceeds source radius")
    tau = np.asarray(tau, dtype=float)
    beta = np.asarray(beta, dtype=float)
    if tau.shape != beta.shape or tau.ndim != 1 or not np.all(np.isfinite(tau + beta)):
        raise ValueError("tau and beta must be finite, equally shaped 1D arrays")
    axis = -half_width + (np.arange(grid_n) + phase) * step
    xx, yy = np.meshgrid(axis, axis)
    z = xx + 1j * yy
    with np.errstate(divide="ignore", invalid="ignore"):
        mapped = z - (1 / (1 + q)) / np.conj(z)
        if q:
            mapped -= (q / (1 + q)) / np.conj(z - s)
    mapped = mapped[np.isfinite(mapped)]
    tree = cKDTree(np.column_stack((mapped.real, mapped.imag)))
    centers = np.column_stack((tau, beta))
    counts = np.array(tree.query_ball_point(centers, r=rho, return_length=True))
    return {"magnification": counts * step**2 / (np.pi * rho**2),
            "counts": counts, "step_over_rho": step / rho,
            "valid_ray_fraction": len(mapped) / (grid_n**2)}


def diagnose_limit(tau, beta, *, q_values, s: float, rho: float,
                   grid_n: int, half_width: float, phases=(0.0, 0.5)):
    """Quantify q->0 bias and grid-phase dependence without claiming convergence."""
    tau = np.asarray(tau, dtype=float)
    beta = np.asarray(beta, dtype=float)
    if tau.shape != beta.shape:
        raise ValueError("trajectory shapes differ")
    reference = finite_source_point_lens(np.hypot(tau, beta), rho)
    rows = []
    for q in q_values:
        for phase in phases:
            shot = ray_shot_magnification(tau, beta, q=float(q), s=s, rho=rho,
                                          grid_n=grid_n, half_width=half_width,
                                          phase=float(phase))
            residual = shot["magnification"] - reference
            rows.append({"q": float(q), "phase": float(phase),
                         "max_absolute_error": float(np.max(np.abs(residual))),
                         "rms_fractional_error": float(np.sqrt(np.mean((residual / reference) ** 2))),
                         "min_ray_count": int(shot["counts"].min()),
                         "step_over_rho": float(shot["step_over_rho"])})
    return {"reference_magnification": reference.tolist(), "diagnostics": rows}
