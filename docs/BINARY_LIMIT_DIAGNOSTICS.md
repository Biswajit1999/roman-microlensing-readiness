# Binary ray-shooting negative-control audit (2026-10-21)

Related: [blocking binary-solver issue #9](https://github.com/Biswajit1999/roman-microlensing-readiness/issues/9) and [independent-solver validation issue #1](https://github.com/Biswajit1999/roman-microlensing-readiness/issues/1).

## Physics and numerical assumptions

The diagnostic uses a **uniform-brightness** circular source of angular radius `rho` (total-mass Einstein-radius units). An independent finite-source point-lens reference integrates the exact Paczyński point-lens magnification over the source disk. The radial primitive is analytic:

`integral A(r) r dr = r sqrt(r² + 4) / 2`.

A Gauss–Legendre angular integral then handles arbitrary impact parameter, including lens-inside-disk and lens-outside-disk geometry. The reference reproduces the exact centered-disk limit `sqrt(rho² + 4) / rho` and the far-field point-source limit in tests.

A second implementation shoots inverse rays using the same binary lens equation but explicitly varies the image-plane **subcell phase** (corner vs cell-centered) and uses `step²` for each cell's area. It preserves zero ray counts rather than masking them with a point-lens floor. The original `magnification_binary_track` is evaluated separately, unmodified. Neither approach is a verified independent fifth-order binary-lens solver.

## Fixed pilot

The script evaluates a fixed four-point source track, `rho=0.06`, `s=1`, mass ratios `q=0`, `10^-6`, `10^-4`, image-grid sizes 220, 360 and 520 per side, and two image-plane grid phases. Source-plane reference uses 256-point angular quadrature. The same track and source radius are used throughout. All data are synthetic; no Roman observations are used.

| Rays/side | Existing solver q=10^-6 max absolute residual | Independent q=0, phase=0 max residual | Independent q=0, phase=0.5 max residual |
|---|---:|---:|---:|
| 220 | 0.33495 | 0.24007 | 0.16996 |
| 360 | 0.34183 | 0.11292 | 0.15698 |
| 520 | 0.05916 | 0.14776 | 0.15588 |

These finite-grid differences demonstrate nontrivial pixel-phase and grid-resolution sensitivity. The selected track **does not reproduce the previously reported worst-case 0.8–1.0 residual**, and therefore neither confirms nor disproves its root cause. The discrepancy at 520 rays is still substantial in some independent-grid phases; no claim of solver convergence is made. The q=10^-4 and q=10^-6 production residuals coincide at the displayed precision for this specific track.

## Reproduce

```bash
python -m pip install -e '.[dev]'
PYTHONPATH=src pytest -q tests/test_rayshoot_diagnostics.py
PYTHONPATH=src python scripts/run_binary_limit_audit.py --output results/binary_limit_pilot.json
python scripts/plot_binary_limit.py --input results/binary_limit_pilot.json --output results/figures/binary_limit_audit.png
```

## Safety gate and next step

**Bound-planet population completeness remains blocked.** Do not enable `configs/planetary.yaml`, alter `results/default/`, or interpret the ray-shooting outputs as validated planetary detections. Before fixing the solver or reopening population runs, cross-check a matched set of `(u, rho, q, s)` configurations against an independent `VBMicrolensing` or `MulensModel` implementation and perform explicit convergence tests across source size and pixel phase. Issues #9 and #1 remain open.
