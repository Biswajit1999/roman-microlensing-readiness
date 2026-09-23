# Limitations

- The six season starts, 70.5-day duration, 12.1-minute cadence, F146 label,
  and six-tile metadata form a versioned public-design proxy. Visibility,
  pointing, detector gaps, weather-like losses, multi-filter sampling, and an
  official simulation product are not modeled.
- The magnitude noise law is phenomenological and not an instrument exposure-
  time calculator. The AR(1) option is generic, not a Roman systematics model.
- The validated injection pathway is an isolated uniform-source point lens.
  Blending is configurable but not population-calibrated. Limb darkening,
  parallax, binary sources, xallarap, orbital motion, and realistic Galactic
  populations are absent from the default experiment.
- The custom binary-lens inverse-ray-shooting implementation fails a required
  vanishing-mass-ratio convergence check. A zero-ray fallback is physically
  invalid. `run_trial` and the CLI therefore refuse planetary runs. The module
  remains only to preserve and diagnose the negative result.
- The blind search uses a finite predeclared timescale bank followed by bounded
  least squares. It is neither a production alert system nor a global posterior
  sampler, and its threshold is not mission-calibrated.
- The v0.5 grid is balanced across a small hand-declared parameter set. It is
  not drawn from a Galactic population, does not integrate over an occurrence
  model, and therefore does not estimate mission completeness or yield.
- A threshold crossing means “event detected.” Accuracy of `t0`, `u0`, and
  `tE` is separately evaluated with declared tolerances.
- Eleven of 900 v0.5 fits failed and are counted as non-detections rather than
  dropped. Runtime is heavy-tailed (0.228 s median, 29.9 s 99th percentile,
  41.4 s maximum on the recorded host). The serial runner does not yet
  checkpoint or parallelize trials.
- Cadence-support and season-edge subgroup summaries are descriptive. Their
  factors are not independently randomized, cell sizes can be small, and no
  multiplicity correction is applied; they are hypothesis-generating, not
  causal estimates.
- Pure Gaussian/AR(1) constant-flux nulls omit variable stars, detector
  artifacts, blends, and non-microlensing transients. Their rate is an internal
  pipeline diagnostic only. Zero triggers in 1,000 trials constrains the rate
  under that simple null; it does not establish a zero false-positive rate.
- The parallax utility consumes observer coordinates in an inertial frame, but
  has not been cross-validated against an independent microlensing package for
  the supplied barycentric ephemeris. It is excluded from default claims.
- Earlier outputs used truth-seeded fitting and obsolete cadence assumptions.
  They are retained for provenance but are scientifically superseded.
