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

A fixed timescale bank proposes data-derived event epochs. Candidates seed
bounded PSPL fits and the lowest-χ² converged fit is selected. Injected truth
does not initialize the search. Event detection uses Δχ² between constant and
PSPL models. Parameter recovery separately evaluates fitted `t0`, `tE`, and
`u0`. Constant-flux nulls undergo the identical search.

Raw rows retain injections, fits, seeds, statistics, endpoints, and failure
reasons. Conditional fractions use two-sided Wilson 95% intervals. Five seeds
per default cell imply broad cell-level uncertainty.
