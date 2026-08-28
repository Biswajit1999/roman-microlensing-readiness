# Methods

## Research question

How do cadence gaps, blending, finite-source effects, parallax, correlated
noise, and selection thresholds change the completeness and false-positive
rate of Roman Galactic Bulge Time Domain Survey (GBTDS) microlensing
searches for bound planets and free-floating planets (FFPs)?

## Null hypothesis

H0: Within the parameter ranges probed, completeness and false-positive rate
for the transparent single-lens detection statistic used here are
insensitive to (do not vary systematically with) survey cadence gaps,
blending fraction, source finite-size (rho), parallax amplitude, correlated
(red) noise amplitude, or the chosen delta-chi2 detection threshold.

This is not expected to hold (the literature, e.g. Penny et al. 2019, is
built entirely around the opposite expectation), and the benchmark's value
is in *quantifying* the rejection of H0 with confidence intervals and an
explicit failure taxonomy, not in the qualitative direction of the effect.

## Physical models (`src/romanmlr/`)

1. **PSPL** (`pspl.py`): exact Paczynski (1986) point-lens magnification,
   `A(u) = (u^2+2) / (u*sqrt(u^2+4))`, with optional Gould (2004) annual/
   orbital parallax computed directly from the Data Challenge ephemeris
   files (no small-parallax series expansion).
2. **FSPL** (`fspl.py`): finite-source correction via direct numerical
   integration of the PSPL magnification over the source disk (uniform
   brightness), rather than a transcribed closed-form elliptic-integral
   solution -- see the module docstring for the correctness rationale.
3. **Binary lens / planetary channel** (`planetary.py`): two-point-mass
   lens magnification via inverse ray shooting (Kayser, Refsdal & Stabell
   1986), which evaluates only the unambiguous forward lens equation. This
   is the project's transparent baseline for the bound-planet channel;
   a full closed-form binary-lens solver (e.g. VBMicrolensing) is a
   documented future cross-validation (`docs/LIMITATIONS.md`).
4. **FFP channel**: modeled as an isolated point lens (PSPL/FSPL), which is
   the physically correct treatment for an unbound lens (no host-star
   deflection to superpose).
5. **Cadence** (`cadence.py`): configurable season structure, downlink
   gaps, and random dropout, defaulting to the Penny et al. (2019) design
   reference (6 seasons x 72 days, 15-minute cadence).
6. **Noise** (`noise.py`): magnitude-dependent white photometric noise plus
   an optional AR(1) correlated-noise term, a deliberately simple,
   documented systematics proxy (not an instrument-team-grade ETC).
7. **Detection statistics** (`detect.py`): bounded nonlinear least-squares
   single-lens fit; event detection via delta-chi2 (flat line -> best-fit
   PSPL); anomaly (planet/FFP) detection via delta-chi2 of the single-lens
   residuals in a window around the perturbation, against the literature-
   standard threshold of 160 (e.g. Gould et al. 2010).

## Experimental design

- **Synthetic injection-recovery** (`injection_recovery.py`,
  `configs/default.yaml`): for each grid point in (u0, tE, rho, [q, s] for
  the planetary channel, source brightness), generate an observation-time
  series from the cadence model, compute the clean model flux, add noise,
  fit a single-lens model, and record detection/anomaly outcomes across
  multiple random seeds. This is the primary experiment: ground truth is
  known exactly by construction.
- **Completeness surfaces** (`completeness.py`): recovery fraction per grid
  bin with a Wilson-score 95% confidence interval, reported alongside
  `n_trials` so under-sampled bins are visible rather than hidden.
- **False-positive rate**: identical cadence/noise pipeline with no
  injected signal (`romanmlr null-fpr`), giving an empirical FPR with a
  Wilson-score interval for the chosen detection threshold.
- **Real-data cross-check**: the 293 events of the 2018 WFIRST/Roman Data
  Challenge (`docs/DATA_SOURCES.md`) provide an external realism check with
  independently simulated cadence/noise and known injected classes,
  including non-microlensing contaminants (cataclysmic variables) to test
  specificity, not just sensitivity.
- **Failure taxonomy**: every trial records a `failure_reason` (e.g.
  `event_below_threshold`, `anomaly_below_threshold`,
  `no_epochs_in_anomaly_window`), preserving *why* recovery failed rather
  than only whether it did.

## What this project does not claim

- No result here is a claim of a real exoplanet, free-floating planet, or
  microlensing detection. All events analyzed by the default pipeline are
  synthetic or are public Data Challenge simulations with known injected
  ground truth.
- The binary-lens ray-shooting model is a numerical approximation with a
  documented resolution floor (`docs/LIMITATIONS.md`), not a certified
  exact solver.
