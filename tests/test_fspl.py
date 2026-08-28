import numpy as np
import pytest

from romanmlr.fspl import magnification_fspl
from romanmlr.pspl import magnification_pspl


def test_fspl_converges_to_point_lens_away_from_source():
    # far from the source disk (u >> rho), finite-source and point-lens
    # magnification must agree closely.
    rho = 0.01
    u = np.array([0.2, 0.5, 1.0, 2.0])
    a_fspl = magnification_fspl(u, rho)
    a_pspl = magnification_pspl(u)
    np.testing.assert_allclose(a_fspl, a_pspl, rtol=2e-3)


def test_fspl_finite_at_u_equal_zero():
    # the point-lens magnification diverges at u=0; the finite-source
    # (uniform disk) magnification must remain finite there.
    rho = 0.05
    a = magnification_fspl(np.array([0.0]), rho)[0]
    assert np.isfinite(a)
    assert a > 1.0


def test_fspl_smaller_than_point_lens_at_small_u():
    # a finite source "smooths over" the central divergence: at u=0 the
    # disk-averaged magnification must be less than the (divergent) point
    # value evaluated at a representative interior point of the disk.
    rho = 0.05
    a_fspl_center = magnification_fspl(np.array([1e-6]), rho)[0]
    a_pspl_center = magnification_pspl(1e-6)
    assert a_fspl_center < a_pspl_center


def test_fspl_rejects_nonpositive_rho():
    with pytest.raises(ValueError):
        magnification_fspl(np.array([0.1]), 0.0)
