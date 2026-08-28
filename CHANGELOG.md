# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-08-28

### Added

- Completed the free-floating-planet (FFP) channel synthetic
  injection-recovery grid (`configs/default.yaml`, 560 trials): 58.0%
  overall recovery, with completeness falling with fainter magnitude and
  larger impact parameter (`results/default/`, `paper/manuscript.md`
  Section 4).
- Matched 200-trial null (no-signal) false-positive-rate estimate: 0/200
  (Wilson 95% CI upper bound 1.9%) at the delta-chi2 > 500 event-detection
  threshold (`results/default/false_positive_rate.json`).
- 8 starter contributor issues filed covering cross-validation, limb
  darkening, the bound-planet-channel population run, adaptive mesh
  refinement, the anomaly-window heuristic, website scoping, Colab
  confirmation, and multi-band fitting.

## [0.1.0] - 2026-08-28

### Added

- Exact point-source point-lens (PSPL) magnification with Gould (2004)
  annual/orbital parallax, validated against hand calculations and the
  zero-parallax limit (`src/romanmlr/pspl.py`).
- Finite-source point-lens (FSPL) magnification via numerical disk
  integration, validated against the point-lens limit
  (`src/romanmlr/fspl.py`).
- Two-point-mass (star + planet) binary-lens magnification via inverse ray
  shooting, validated against the vanishing-mass-ratio and wide-separation
  analytic limits (`src/romanmlr/planetary.py`).
- Free-floating-planet channel modeled as an isolated point lens.
- Roman GBTDS-like observing-cadence generator with configurable season
  structure, downlink gaps, and random dropout (`src/romanmlr/cadence.py`).
- Photometric noise model (magnitude-dependent white noise + optional AR(1)
  correlated noise) (`src/romanmlr/noise.py`).
- Transparent single-lens detection statistics (event and anomaly delta-chi2)
  with literature-standard thresholds (`src/romanmlr/detect.py`).
- Adapter for the public 2018 WFIRST/Roman Microlensing Data Challenge, with
  checksum-manifested caching (`src/romanmlr/data.py`).
- Injection-recovery engine and completeness/false-positive-rate estimation
  with Wilson-score confidence intervals
  (`src/romanmlr/injection_recovery.py`, `src/romanmlr/completeness.py`).
- Command-line workflow (`romanmlr fetch-data`, `romanmlr run-grid`,
  `romanmlr null-fpr`).
- Test suite (30 fast tests + 3 slower ray-shooting validation tests).

### Known limitations

See `docs/LIMITATIONS.md`. Notably: the binary-lens solver is a Monte-Carlo
ray-shooting method, not an exact closed-form solver, and has a resolution
floor for very small mass ratios; the planetary anomaly-window heuristic and
the noise model are documented simplifications.
