"""Seed-free q->0 / grid-phase / resolution audit of the existing ray shooter.

This is a negative-control diagnostic, NOT a planetary completeness run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from romanmlr.planetary import BinaryLensConfig, magnification_binary_track
from romanmlr.rayshoot_diagnostics import diagnose_limit, finite_source_point_lens


def run():
    tau = np.array([0.0, 0.08, 0.16, 0.28])
    beta = np.full_like(tau, 0.10)
    rho = 0.06
    reference = finite_source_point_lens(np.hypot(tau, beta), rho, n_phi=256)
    experiments = {}
    for n in (220, 360, 520):
        half = 3.0 + 6 * rho
        diag = diagnose_limit(tau, beta, q_values=(0.0, 1e-6, 1e-4),
                              s=1.0, rho=rho, grid_n=n, half_width=half,
                              phases=(0.0, 0.5))
        original = {}
        for q in (1e-6, 1e-4):
            cfg = BinaryLensConfig(q=q, s=1.0, rho=rho, grid_n=n,
                                   box_half_width=half)
            mag = magnification_binary_track(tau, beta, cfg)
            original[str(q)] = {
                "magnification": mag.tolist(),
                "max_absolute_error": float(np.max(np.abs(mag - reference))),
                "rms_fractional_error": float(np.sqrt(np.mean(((mag - reference) / reference) ** 2))),
            }
        experiments[str(n)] = {"independent_grid": diag["diagnostics"],
                               "production_solver": original}
    return {"trajectory_tau": tau.tolist(), "trajectory_beta": beta.tolist(),
            "rho": rho, "reference": reference.tolist(), "results": experiments,
            "warning": "Diagnostic only. The bound-planet channel remains blocked by issue #9; "
                       "no independent VBMicrolensing/pyLIMA comparison has been performed."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "grid_sizes": list(result["results"])}))


if __name__ == "__main__":
    main()
