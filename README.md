# Roman Microlensing Readiness Benchmark

[![CI](https://github.com/Biswajit1999/roman-microlensing-readiness/actions/workflows/ci.yml/badge.svg)](https://github.com/Biswajit1999/roman-microlensing-readiness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A transparent injection-recovery benchmark for the Nancy Grace Roman Space
Telescope Galactic Bulge Time Domain Survey (GBTDS): how do cadence gaps,
blending, finite-source effects, parallax, correlated noise, and detection
thresholds change the completeness and false-positive rate of bound-planet
and free-floating-planet (FFP) microlensing searches?

This is a **benchmark and methods study**, not a discovery pipeline. Every
event analyzed by the default configuration is either a synthetic injection
with known ground truth, or a public, pre-launch simulated dataset (the
2018 WFIRST/Roman Microlensing Data Challenge). See `docs/CLAIMS.md` for the
full claims ledger and `docs/LIMITATIONS.md` for known failure modes.

## Why this exists

Roman's GBTDS is expected to find on the order of 10^4-10^5 exoplanets via
microlensing (Penny et al. 2019), including the first statistically
meaningful sample of free-floating planets (Johnson et al. 2020). Yield
forecasts exist; a small, reusable, independently-implemented benchmark for
*how survey design choices trade off completeness against false positives*
-- with an explicit, inspectable failure taxonomy -- does not yet exist as
open, reproducible software. This project is a step toward one, scoped to
what a single transparent single-lens detection pipeline can honestly claim.

## Quickstart

```bash
git clone https://github.com/Biswajit1999/roman-microlensing-readiness.git
cd roman-microlensing-readiness
python -m pip install -e ".[dev]"

pytest -q                                   # 30 fast tests, < 10 s
pytest -q -m slow                            # + 3 physics-limit validation tests

romanmlr run-grid --config configs/smoke_test.yaml --out results/smoke
```

See `docs/REPRODUCIBILITY.md` for the full-experiment reproduction command
and `notebooks/` for a Colab-ready walkthrough.

## What's implemented

- **Exact point-lens (PSPL) magnification** with Gould (2004) parallax,
  computed directly from the real Data-Challenge spacecraft ephemeris.
- **Finite-source (FSPL) magnification** via numerical disk integration
  (no transcribed closed-form elliptic-integral risk; see
  `src/romanmlr/fspl.py`).
- **Two-point-mass binary-lens magnification** via inverse ray shooting
  for the bound-planet channel, and an isolated-point-lens model for the
  free-floating-planet channel (the physically correct treatment for an
  unbound lens).
- **Roman-GBTDS-like cadence model** (configurable seasons, downlink gaps,
  dropout) and a **magnitude-dependent + correlated (AR(1)) noise model**.
- **Transparent single-lens detection statistics** (event and anomaly
  delta-chi2) against literature-standard thresholds.
- **Injection-recovery engine** producing completeness and false-positive-
  rate surfaces with Wilson-score confidence intervals, plus a
  per-trial failure taxonomy (why a given injection was missed).
- **A real-data adapter** for the public 2018 WFIRST/Roman Microlensing
  Data Challenge (293 events, four classes including non-microlensing
  contaminants), used as an external realism cross-check.

Every physical model above is checked against at least one analytically
known limit or hand calculation -- see `docs/VALIDATION.md` for the full
table and `tests/` for the re-runnable checks.

## What this is not

- Not a claim of any real exoplanet, free-floating-planet, or microlensing
  detection.
- Not an official Roman/RGES-PIT product; not affiliated with or endorsed
  by NASA, STScI, or the RGES Project Infrastructure Team.
- Not a certified-precision binary-lens solver -- the ray-shooting method
  has a documented resolution floor (`docs/LIMITATIONS.md`); do not use it
  for a precision fit of a real candidate event.
- Not a submission to the live Roman Microlensing Data Challenge 2026
  (RMDC26); see `docs/DATA_SOURCES.md`.

## Repository layout

```
src/romanmlr/     physical models, cadence/noise, detection, injection-recovery, CLI
tests/            unit + validation tests (pytest markers: slow, network)
configs/          experiment configs (YAML)
docs/             METHODS, DATA_SOURCES, LIMITATIONS, REPRODUCIBILITY, VALIDATION, CLAIMS
notebooks/        Colab-ready walkthrough
paper/            methods manuscript
results/          generated outputs only (see results/README.md)
```

## Citation

See `CITATION.cff`. This project builds on and cites Penny et al. (2019,
ApJS 241, 3), Johnson et al. (2020, AJ 160, 123), and the public 2018
WFIRST/Roman Microlensing Data Challenge (Penny et al.,
<https://github.com/microlensing-data-challenge/data-challenge-1>).

## Contributing

See `CONTRIBUTING.md`. Issues and replication attempts are welcome.

## Acknowledgments

See `ACKNOWLEDGMENTS.md` for development-tooling and data-provenance
acknowledgments.
