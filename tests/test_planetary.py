import numpy as np
import pytest

from romanmlr.fspl import magnification_fspl
from romanmlr.planetary import BinaryLensConfig, magnification_binary_track
from romanmlr.pspl import magnification_pspl


@pytest.mark.slow
def test_vanishing_mass_ratio_matches_single_lens():
    """q -> 0 must reduce to the finite-source point-lens magnification of
    the primary alone (the planet contributes negligible deflection)."""
    rho = 0.02
    cfg = BinaryLensConfig(q=1e-6, s=1.0, rho=rho, grid_n=500)
    tau = np.array([0.0, 0.1, 0.3])
    beta = np.full(3, 0.1)
    a_binary = magnification_binary_track(tau, beta, cfg)
    u = np.sqrt(tau**2 + beta**2)
    a_single = magnification_fspl(u, rho)
    # ray-shooting has O(1/sqrt(N_rays)) Monte-Carlo-like scatter; grid_n=500
    # (250000 rays) is tuned for ~few-percent agreement in this test.
    np.testing.assert_allclose(a_binary, a_single, rtol=0.08)


@pytest.mark.slow
def test_wide_separation_matches_two_decoupled_lenses():
    """For s >> 1 the binary-lens magnification of a source near the
    primary must reduce to the primary's own point-lens magnification,
    since the companion is far outside the region probed by the trajectory
    (flux contribution from the distant second lens is negligible there)."""
    rho = 0.02
    s = 8.0
    cfg = BinaryLensConfig(q=0.05, s=s, rho=rho, grid_n=600, box_half_width=12.0)
    tau = np.array([0.0, 0.05])
    beta = np.array([0.05, 0.1])
    a_binary = magnification_binary_track(tau, beta, cfg)
    u = np.sqrt(tau**2 + beta**2)
    a_primary_only = magnification_pspl(u)
    np.testing.assert_allclose(a_binary, a_primary_only, rtol=0.1)
