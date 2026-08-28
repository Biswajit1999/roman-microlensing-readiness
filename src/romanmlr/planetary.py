"""Two-point-mass (star + bound planet) lens magnification via inverse ray
shooting, and the free-floating-planet (FFP) channel as an isolated point lens.

Design rationale
-----------------
A full analytic binary-lens solver requires locating images as roots of a
complex fifth-order polynomial (Witt 1990) whose coefficients are easy to
mis-transcribe from memory -- exactly the silent-equation-error risk this
project's research standard is built to avoid. Inverse ray shooting (Kayser,
Refsdal & Stabell 1986; Wambsganss 1997, "Gravitational Lensing in
Astronomy") instead evaluates only the forward lens equation

    zeta = z - m1/conj(z - z1) - m2/conj(z - z2)

(mass fractions m1 + m2 = 1, star at z1, planet at z2 = s along the real
axis, separation s in Einstein radii of the *total* system mass -- the
standard Mao & Paczynski 1991 / Gould & Loeb 1992 convention), which has no
sign or branch ambiguity. It is a Monte-Carlo/grid method rather than an
exact closed-form solver, so it is slower and has a resolution floor; both
are treated as documented limitations (see docs/LIMITATIONS.md), and its
correctness is checked against two analytic limits in tests/test_planetary.py:

  1. q -> 0 (planet mass -> 0) must reduce to the finite-source point-lens
     magnification in fspl.py.
  2. s >> 1 (very wide separation) must reduce to the sum of two independent,
     decoupled point-lens magnifications minus 1 (flux conservation of two
     well-separated lenses).

Free-floating planets are not gravitationally bound to a host star, so they
are correctly modeled as isolated point lenses (no binary-lens machinery
needed); see fspl.py / pspl.py and Johnson et al. (2020, AJ 160, 123).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from .fspl import magnification_fspl
from .pspl import magnification_pspl


@dataclass(frozen=True)
class BinaryLensConfig:
    q: float          # planet/star mass ratio, m_planet / m_star
    s: float          # projected separation, Einstein radii of total mass
    rho: float        # source radius, Einstein radii of total mass
    grid_n: int = 800  # rays per side (grid_n**2 total rays)
    box_half_width: float | None = None  # image-plane half-width; auto if None


def _default_box_half_width(cfg: BinaryLensConfig) -> float:
    return max(3.0, 1.8 * cfg.s) + 6 * cfg.rho


def build_ray_shot_tree(cfg: BinaryLensConfig) -> tuple[cKDTree, float, int]:
    """Shoot a uniform grid of rays through the binary lens once.

    Returns (tree over mapped source-plane positions, image-plane cell area,
    number of rays). Reuse the same tree for every epoch of one light curve.
    """
    half_check = cfg.box_half_width or _default_box_half_width(cfg)
    cell_size = 2 * half_check / cfg.grid_n
    if cell_size > cfg.rho:
        # A source disk smaller than a single image-plane grid cell is
        # severely undersampled: the ray count landing inside it becomes
        # essentially random (0, 1, a few...), which can produce a
        # spuriously large or small magnification rather than a merely
        # imprecise one -- caught during development by comparing a
        # ray-shot light curve against the analytic point-lens q->0 limit
        # and finding a ~3x spurious spike near peak magnification for
        # rho=0.005, grid_n=250 (see docs/VALIDATION.md). Raise rather
        # than silently return an unreliable number.
        raise ValueError(
            f"rho={cfg.rho} is smaller than the ray-shooting cell size "
            f"({cell_size:.4g}, from grid_n={cfg.grid_n}); increase grid_n or rho "
            f"until cell_size <= rho (see docs/LIMITATIONS.md)."
        )

    m1 = 1.0 / (1.0 + cfg.q)
    m2 = cfg.q / (1.0 + cfg.q)
    z1 = 0.0 + 0.0j
    z2 = cfg.s + 0.0j

    half = cfg.box_half_width or _default_box_half_width(cfg)
    axis = np.linspace(-half, half, cfg.grid_n)
    cell_area = (2 * half / cfg.grid_n) ** 2

    xx, yy = np.meshgrid(axis, axis)
    z = xx + 1j * yy
    with np.errstate(divide="ignore", invalid="ignore"):
        zeta = z - m1 / np.conj(z - z1) - m2 / np.conj(z - z2)
    zeta = zeta[np.isfinite(zeta)]

    pts = np.column_stack([zeta.real, zeta.imag])
    tree = cKDTree(pts)
    return tree, cell_area, cfg.grid_n * cfg.grid_n


def magnification_binary_track(
    tau: np.ndarray, beta: np.ndarray, cfg: BinaryLensConfig
) -> np.ndarray:
    """Finite-source binary-lens magnification along a source trajectory.

    ``tau``/``beta`` are the source-plane coordinates (see pspl.trajectory)
    in the same primary-centered frame as ``cfg`` (star at the origin).
    """
    tree, cell_area, n_rays = build_ray_shot_tree(cfg)
    tau = np.asarray(tau, dtype=float)
    beta = np.asarray(beta, dtype=float)
    counts = np.array(
        [len(tree.query_ball_point([tp, bp], r=cfg.rho)) for tp, bp in zip(tau, beta)]
    )
    source_area = np.pi * cfg.rho**2
    mag = (counts.astype(float) / n_rays) * (
        (cell_area * n_rays) / source_area
    )  # == counts/n_rays * total_image_area / source_area

    # A count of exactly zero means no shot ray happened to land inside the
    # (typically tiny) source disk -- a finite-ray-density undersampling
    # artifact, not a physical demagnification-to-zero (real lens systems
    # generically stay of order unity magnification almost everywhere; see
    # docs/LIMITATIONS.md). Floor those points at the primary-alone
    # point-lens magnification, which is a safe physically motivated lower
    # bound for q << 1 and is exact in the q -> 0 limit tested in
    # tests/test_planetary.py.
    zero = counts == 0
    if np.any(zero):
        u_primary = np.sqrt(tau[zero] ** 2 + beta[zero] ** 2)
        mag[zero] = np.maximum(mag[zero], magnification_pspl(u_primary))
    return mag


def free_floating_planet_magnification(u: np.ndarray, rho: float | None) -> np.ndarray:
    """FFP magnification: an isolated point lens (not bound to a host star).

    Uses the finite-source model when ``rho`` is given, else the exact
    point-lens formula.
    """
    if rho is None or rho <= 0:
        return magnification_pspl(u)
    return magnification_fspl(u, rho)
