import numpy as np
import pytest
from romanmlr.limb_darkening import (
    linear_source_magnification, exposure_averaged_magnification, quadrature_convergence
)


def test_center_uniform_matches_exact_finite_source_formula():
    # A_FSPL(u=0) = sqrt(rho^2+4)/rho for uniform surface brightness.
    rho = 0.08
    actual = linear_source_magnification(np.array([0.0]), rho, 0, n_radial=96, n_angular=192)[0]
    expected = np.sqrt(rho*rho+4)/rho
    assert np.isclose(actual, expected, rtol=2e-5)


def test_center_brightening_increases_peak():
    u = np.array([0.0])
    uniform = linear_source_magnification(u, 0.08, 0.0)[0]
    darkened = linear_source_magnification(u, 0.08, 0.6)[0]
    assert darkened > uniform


def test_off_axis_far_field_is_nearly_independent_of_limb_law():
    u = np.array([1.5])
    a = linear_source_magnification(u, 0.01, 0.0)[0]
    b = linear_source_magnification(u, 0.01, 0.8)[0]
    assert abs(a-b) < 1e-5


def test_scalar_shape_and_array_shape():
    assert np.shape(linear_source_magnification(0.1, 0.02, 0.4)) == ()
    assert linear_source_magnification(np.array([0.1,0.2]),0.02,0.4).shape == (2,)


@pytest.mark.parametrize('rho,c', [(0,0.5),(-1,0.2),(0.1,-0.1),(0.1,1.1),(0.1,np.nan)])
def test_invalid_source_parameters(rho,c):
    with pytest.raises(ValueError):
        linear_source_magnification([0.0],rho,c)


def test_invalid_separation():
    with pytest.raises(ValueError):
        linear_source_magnification([-0.01],0.1,0.3)


def test_exposure_zero_matches_instantaneous():
    t=np.array([-0.02,0.0,0.02])
    a=exposure_averaged_magnification(t,t0=0,t_e=0.5,u0=0.1,rho=0.02,
                                       coefficient=0.3,exposure_days=0)
    b=linear_source_magnification(np.hypot(t/0.5,0.1),0.02,0.3,n_radial=32,n_angular=96)
    np.testing.assert_allclose(a,b,rtol=1e-12)


def test_symmetric_peak_is_reduced_by_long_exposure():
    params=dict(t0=0,t_e=0.2,u0=0.01,rho=0.04,coefficient=0.5)
    short=exposure_averaged_magnification(np.array([0.0]),exposure_days=0,**params)[0]
    long=exposure_averaged_magnification(np.array([0.0]),exposure_days=0.03,n_time=9,**params)[0]
    assert long < short


def test_quadrature_convergence_at_center():
    out=quadrature_convergence(np.array([0.0]),0.05,0.6,orders=(16,32,64))
    assert out['magnification'].shape==(3,1)
    assert out['relative_change'][-1,0] < out['relative_change'][0,0]
    assert out['relative_change'][-1,0] < 0.001


def test_reject_bad_time_integration():
    with pytest.raises(ValueError):
        exposure_averaged_magnification([0.0],t0=0,t_e=0,u0=0.1,rho=0.1,
                                         coefficient=0.5,exposure_days=0)
