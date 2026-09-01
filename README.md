# Synthetic Point-Lens Microlensing Recovery Study

[![CI](https://github.com/Biswajit1999/roman-microlensing-readiness/actions/workflows/ci.yml/badge.svg)](https://github.com/Biswajit1999/roman-microlensing-readiness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An independent experiment for measuring recovery of synthetic point-lens
events under a declared Roman-motivated season/cadence and phenomenological
noise model. It is not an official Roman product, readiness assessment,
mission forecast, discovery pipeline, or analysis of Roman flight data.

The repository slug is retained so existing links continue to work. The
display name is narrower because “readiness” was not supported by the scope.

## Post-audit changes

- Replaced six consecutive 72-day seasons and invented downlink/dropout gaps
  with an explicit, version-labelled public-design proxy: six 70.5-day seasons,
  three early and three late, at 12.1-minute F146 cadence.
- Event epochs are sampled across seasons rather than fixed at day 30.
- The detection fit is initialized by a blind data search, never injected
  `t0`, `u0`, or `tE`; nulls use the identical search space.
- Event detection and parameter recovery are separate raw outputs.
- Null trials are committed individually, with a scoped summary.
- The custom binary-lens pathway is disabled. Its non-convergent solver and
  zero-ray fallback are not valid evidence for planetary recovery.
- Config copies and environment/commit manifests accompany each run.

Earlier `results/default/` numbers came from a truth-seeded fit and superseded
cadence/noise assumptions. They are historical artifacts and are not current
scientific claims.

## Reproduce

```bash
python -m pip install -e ".[dev]"
pytest -q
romanmlr run-grid --config configs/smoke_test.yaml --out results/post_audit_smoke
romanmlr null-fpr --config configs/smoke_test.yaml --out results/post_audit_null --n-trials 50
```

The smoke configuration verifies software only. A full exploratory run uses
`configs/default.yaml`; its results must be reviewed before prose claims are
added. See [limitations](docs/LIMITATIONS.md), [claims](docs/CLAIMS.md), and
[reproducibility](docs/REPRODUCIBILITY.md).

## Affiliation and marks

“Roman” and “F146” are used descriptively. This independent project is not
affiliated with or endorsed by NASA, STScI, IPAC, GSFC, or the Roman project.
