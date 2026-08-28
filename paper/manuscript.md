# Roman Microlensing Readiness Benchmark: Methods and Status

**Author**: Biswajit Jana
**Status**: Living methods document (v0.1) -- describes the implemented
software and its validation. Does **not** yet report a completed
population-scale completeness/false-positive-rate result; see "Status of
results" below.

## Abstract

We describe an open, independently implemented injection-recovery benchmark
for microlensing exoplanet searches under a Nancy Grace Roman Space
Telescope Galactic Bulge Time Domain Survey (GBTDS)-like cadence. The
benchmark separates a transparent point-lens/finite-source baseline from a
ray-shooting two-point-mass binary-lens model for bound planets, treats
free-floating planets as isolated point lenses, and quantifies completeness
and false-positive rate with Wilson-score confidence intervals across a
configurable grid of impact parameter, Einstein-crossing time, source size,
survey cadence, and detection threshold. Every physical model is validated
against an analytically known limit rather than only against itself. We
report the validated software and its limitations; a population-scale
completeness/false-positive-rate result over the full parameter grid in
`configs/default.yaml`, and any comparison to previously published Roman
yield forecasts, is future work tracked in `PORTFOLIO_PROGRESS.md`.

## 1. Introduction

[To be expanded with a literature review once Stage F (independent-quality
audit) begins; see `docs/METHODS.md` for the research question and null
hypothesis as currently stated, and `docs/DATA_SOURCES.md` for the primary
citations this project relies on to date: Penny et al. (2019), Johnson et
al. (2020), and the 2018 WFIRST/Roman Microlensing Data Challenge.]

## 2. Methods

See `docs/METHODS.md` for the complete, current description of the physical
models, cadence/noise models, detection statistics, and experimental
design. That file is the authoritative methods reference; this section will
be synchronized with it before any results section is added.

## 3. Validation

See `docs/VALIDATION.md` for the complete table of checks performed against
analytic limits and hand calculations, and `docs/LIMITATIONS.md` for
documented approximations and their expected impact.

## 4. Status of results

No population-scale injection-recovery grid has been executed and reviewed
at the time of this commit. `configs/smoke_test.yaml` has been run
end-to-end as a pipeline sanity check (`results/smoke/`, regenerated in
CI); `configs/default.yaml` defines the intended full experiment and has
not yet been executed at scale. This section, and an accompanying results
section with completeness/false-positive-rate figures, will be added once
that run is complete and reviewed, per `docs/CLAIMS.md` item 9 (no number
in this repository is typed by hand).

## 5. Limitations

See `docs/LIMITATIONS.md`.

## Acknowledgments

See `ACKNOWLEDGMENTS.md`.
