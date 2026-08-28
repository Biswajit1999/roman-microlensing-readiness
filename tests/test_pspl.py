import numpy as np
import pytest

from romanmlr.pspl import PSPLParams, magnification_pspl, trajectory


def test_magnification_hand_calculation():
    # A(u=1) = (1+2) / (1*sqrt(1+4)) = 3/sqrt(5)
    assert magnification_pspl(1.0) == pytest.approx(3.0 / np.sqrt(5.0), rel=1e-12)
    # A(u=0.5): (0.25+2)/(0.5*sqrt(0.25+4)) = 2.25/(0.5*sqrt(4.25))
    assert magnification_pspl(0.5) == pytest.approx(2.25 / (0.5 * np.sqrt(4.25)), rel=1e-12)


def test_magnification_limits():
    # far from the lens, magnification -> 1
    assert magnification_pspl(1000.0) == pytest.approx(1.0, abs=1e-5)
    # close to the lens, magnification diverges like ~1/u
    a_small = magnification_pspl(1e-4)
    assert a_small > 1e3
    # magnification is monotonically decreasing in u
    u = np.linspace(0.01, 5, 200)
    a = magnification_pspl(u)
    assert np.all(np.diff(a) < 0)


def test_trajectory_no_parallax_matches_linear_motion():
    t = np.linspace(-50, 50, 501)
    p = PSPLParams(t0=0.0, u0=0.1, tE=20.0)
    u = trajectory(t, p)
    tau = t / p.tE
    expected = np.sqrt(tau**2 + p.u0**2)
    np.testing.assert_allclose(u, expected, rtol=1e-12)


def test_parallax_requires_ephemeris():
    t = np.linspace(-50, 50, 11)
    p = PSPLParams(t0=0.0, u0=0.1, tE=20.0, piEN=0.1, piEE=0.05)
    with pytest.raises(ValueError):
        trajectory(t, p)


def test_parallax_vanishes_as_pie_shrinks():
    """As |piE| -> 0 the parallax-corrected trajectory must converge to the
    unperturbed straight-line trajectory (Gould 2004 formalism reduces
    smoothly to the piE=0 case)."""
    t = np.linspace(-50, 50, 51)
    tt = np.linspace(-100, 100, 400)
    ephem = {
        "t": tt,
        "xyz": np.column_stack(
            [np.cos(tt / 365.25 * 2 * np.pi), np.sin(tt / 365.25 * 2 * np.pi), np.zeros(tt.size)]
        ),
    }
    p0 = PSPLParams(t0=0.0, u0=0.1, tE=20.0)
    u0 = trajectory(t, p0)

    errors = []
    for pie in (1e-2, 1e-3, 1e-4):
        p = PSPLParams(t0=0.0, u0=0.1, tE=20.0, piEN=pie, piEE=pie)
        u = trajectory(t, p, ephem=ephem, ra_deg=270.0, dec_deg=-29.0)
        errors.append(np.max(np.abs(u - u0)))
    # deviation from the unperturbed trajectory shrinks roughly linearly with piE
    assert errors[0] > errors[1] > errors[2]
    assert errors[2] < 1e-3
