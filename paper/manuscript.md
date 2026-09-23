# Blind recovery is not parameter identifiability in short synthetic microlensing events

**Author:** Biswajit Jana

**Version:** 0.5.0

**Status:** reproducible software methods result; not peer reviewed

## Abstract

We measure blind recovery of 900 synthetic isolated point-lens events under an
explicit Roman-motivated observing-window and white-noise proxy. A data-driven
matched filter proposes an event, a bounded point-source point-lens fit is run
without injected parameters, and detection is separated from recovery of the
injected `t0`, `u0`, and `tE`. The search detects 864/900 events (96.0%, Wilson
95% CI 94.5–97.1%) but recovers the declared parameters in only 710/900 (78.9%,
76.1–81.4%). At F146=24 and `tE=0.02 d`, the corresponding fractions are
41/75 (54.7%) and 22/75 (29.3%). An identical search of 1,000 simple constant-
flux nulls triggers zero times (95% upper bound 0.383%). These are conditional
software-selection results, not Roman mission completeness, yield, readiness,
or survey false-positive estimates.

## 1. Research question and estimand

The question is whether crossing a blind event-detection threshold implies
that the short event's physical light-curve parameters are identifiable under
the same synthetic cadence/noise proxy. The estimands are the detection and
parameter-recovery fractions in a balanced declared grid. The denominator is
the injected grid—not a Galactic population—and all fit failures remain in it.

## 2. Experimental design

The experiment crosses F146 reference magnitude `{19, 22, 24}`, impact
parameter `{0.1, 0.6, 1.0}`, and Einstein crossing time
`{0.02, 0.08, 0.3, 1.0}` days, with 25 independently seeded replicates per
full cell. Event peaks are sampled uniformly within one of six configured
70.5-day seasons. Observations use 12.1-minute sampling and a phenomenological
magnitude-dependent white-noise law. These values are a versioned public-
design proxy, not an operations simulation.

A SHA-256-derived master seed is unique to experiment, parameter cell, and
replicate. `SeedSequence` creates independent cadence, epoch, and noise
streams. Raw outputs retain every seed and fitted/injected parameter.

## 3. Blind search and endpoints

For each predeclared timescale, a time-aware boxcar statistic is evaluated on
the full light curve. The highest-scoring proposal seeds one bounded PSPL fit
on a local window with deterministic baseline anchors. Final model χ² is
evaluated on all original epochs. No injected parameter initializes the
search, and the identical search space is used for nulls.

Detection requires Δχ² > 500 against a weighted constant model. Parameter
recovery additionally requires `t0` within the larger of 0.1 `tE` or one
cadence, `tE` within 50%, and `u0` within 0.2. Binomial fractions use two-sided
Wilson 95% intervals.

## 4. Results

The search detects 864/900 injections (96.0%, CI 94.5–97.1%) and recovers
parameters in 710/900 (78.9%, CI 76.1–81.4%). Conditional on detection,
710/864 recover parameters (82.2%, CI 79.5–84.6%). Eleven fits fail and count
as non-detections.

The gap widens at the faint, short boundary. At F146=24 and `tE=0.02 d`,
41/75 are detected (54.7%, CI 43.4–65.4%) but 22/75 recover parameters
(29.3%, CI 20.2–40.4%). When grouped by realized cadence support, parameter
recovery is 134/225 (59.6%) for 3–9 epochs within one `tE`, 167/225 (74.2%)
for 10–29, and 409/450 (90.9%) for at least 30. These strata co-vary with
timescale and are descriptive rather than causal.

The identical search produces 0/1,000 triggers on simple constant-flux nulls,
with Wilson 95% upper bound 0.383%. This does not include astrophysical or
instrumental impostors and must not be called the Roman false-positive rate.

## 5. Negative result and claim boundary

The repository's custom inverse-ray-shooting binary-lens implementation fails
a required vanishing-mass-ratio convergence check and contains an invalid
zero-ray fallback. Planetary inference is therefore blocked at runtime. No
bound-planet result is included or inferred from the point-lens experiment.

## 6. Reproducibility and limitations

The release commits raw trial and null rows, copied configs, endpoint tables,
input hashes, environment manifests, figures, and the generating script. Both
primary manifests identify clean source commit `4dfb89f`. The cadence, noise,
population, null, and search models remain simplified; see
`docs/LIMITATIONS.md`. Independent validation against a maintained
microlensing package and realistic variable/artifact null ensembles are the
highest-priority next steps.
