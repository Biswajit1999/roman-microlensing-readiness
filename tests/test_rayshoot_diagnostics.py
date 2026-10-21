import numpy as np
import pytest

from romanmlr.rayshoot_diagnostics import (
    diagnose_limit, finite_source_point_lens, ray_shot_magnification,
)


@pytest.mark.parametrize("rho", [0.01, 0.04, 0.2])
def test_centered_source_has_exact_closed_form(rho):
    actual = finite_source_point_lens(np.array([0.0]), rho)[0]
    assert actual == pytest.approx(np.sqrt(rho**2 + 4) / rho, rel=1e-12)


def test_far_field_approaches_point_source():
    u, rho = 2.0, 0.001
    actual = finite_source_point_lens(np.array([u]), rho)[0]
    exact = (u**2 + 2) / (u * np.sqrt(u**2 + 4))
    assert actual == pytest.approx(exact, rel=1e-5)


def test_scalar_and_vector_consistent():
    assert finite_source_point_lens(0.2, 0.05) == pytest.approx(
        finite_source_point_lens(np.array([0.2]), 0.05)[0]
    )


def test_lens_magnification_is_at_least_unity():
    u = np.array([0.0, 0.03, 0.1, 0.5, 1.0])
    assert np.all(finite_source_point_lens(u, 0.04) >= 1)


def test_ray_shot_counts_and_phase_differ():
    kwargs = dict(q=0, s=1.0, rho=0.08, grid_n=180, half_width=3.0)
    a = ray_shot_magnification([0.0, 0.15], [0.1, 0.1], phase=0, **kwargs)
    b = ray_shot_magnification([0.0, 0.15], [0.1, 0.1], phase=0.5, **kwargs)
    assert a["counts"].shape == (2,)
    assert np.all(a["magnification"] >= 0)
    assert a["valid_ray_fraction"] > 0.99
    assert not np.array_equal(a["counts"], b["counts"])


def test_limit_returns_independent_q_and_phase_rows():
    out = diagnose_limit(np.array([0.0, 0.2]), np.array([0.1, 0.1]),
                         q_values=[0, 1e-6], s=1.0, rho=0.08,
                         grid_n=180, half_width=3.0)
    assert len(out["diagnostics"]) == 4
    assert all(np.isfinite(x["rms_fractional_error"]) for x in out["diagnostics"])
    assert all(x["step_over_rho"] < 1 for x in out["diagnostics"])


@pytest.mark.parametrize("bad", [0.0, -0.1, float("nan")])
def test_invalid_radius_rejected(bad):
    with pytest.raises(ValueError):
        finite_source_point_lens([0.1], bad)


def test_ray_shot_rejects_undersampling():
    with pytest.raises(ValueError, match="spacing"):
        ray_shot_magnification([0.1], [0.1], q=0, s=1, rho=0.005,
                               grid_n=100, half_width=3)


def test_mismatched_trajectory_rejected():
    with pytest.raises(ValueError):
        ray_shot_magnification([0.1, 0.2], [0.1], q=0, s=1, rho=0.1,
                               grid_n=100, half_width=3)
