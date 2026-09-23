# Methods

## Estimand

The endpoint is the conditional recovery fraction of the explicitly sampled
synthetic point-lens grid under this software pipeline. The denominator is the
set of injected trials in each declared bin. It is not population-weighted
survey completeness, yield, readiness, reliability, or precision.

## Injection, window, and noise

Each trial declares `u0`, `tE`, uniform-source radius, source/blend flux,
reference magnitude, and RNG seed. Unless fixed, an event epoch is drawn in a
random configured season. The default uses a uniform-source isolated point
lens. Planetary execution is blocked.

The cadence records explicit season starts, duration, sampling, filter label,
tile-count metadata, dropout, and a survey-definition identifier. It is an
incomplete F146 high-cadence proxy, not an operations simulation. Noise combines
a floor with a photon-limited 10^(0.2 Δmag) term; AR(1) noise is optional.

## Blind search and endpoints

A fixed timescale bank is scanned with a time-aware boxcar statistic. The
highest-significance data-derived `(t0, tE)` proposal seeds one bounded PSPL
fit on a deterministic local window plus sparse baseline anchors. The fitted
model's χ² is then evaluated on every original epoch, so local fitting changes
cost but not the detection statistic's denominator. Injected truth does not
initialize or bound the search. Constant-flux nulls undergo the identical
look-elsewhere procedure.

Event detection uses Δχ² between the weighted constant model and the blind
PSPL fit. Parameter recovery is a stricter, separate endpoint: a detected
event must recover `t0` to the larger of 0.1 tE or one cadence, `tE` within
50%, and `u0` within 0.2. These tolerances are predeclared software-study
criteria, not mission requirements.

## Randomization and v0.5 design

Each grid trial receives a stable SHA-256-derived master seed keyed by the
experiment identifier, injected parameters, and replicate number. NumPy
`SeedSequence` then creates independent cadence, event-epoch, and photometric-
noise streams. All four seeds are retained in the raw table. This prevents
the earlier reuse of seed 0-4 in every cell while preserving exact replay.

`configs/cadence_phase_v0.5.yaml` crosses three reference magnitudes, three
impact parameters, and four crossing times with 25 replicates (900 total).
The primary `(magnitude, tE)` summaries pool the three predeclared `u0` values,
giving n=75 per reported cell. This is a balanced conditional grid, not a
draw from a Galactic population. The matched null experiment uses 1,000
constant-flux realizations at F146=22.

Raw rows retain injections, fits, seeds, statistics, endpoints, and failure
reasons, plus nearest-epoch phase, epochs within one tE, and normalized season-
edge distance. Conditional fractions use two-sided Wilson 95% intervals.
