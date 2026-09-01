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
- A threshold crossing means “event detected.” Accuracy of `t0`, `u0`, and
  `tE` is separately evaluated with declared tolerances.
- Pure Gaussian/AR(1) constant-flux nulls omit variable stars, detector
  artifacts, blends, and non-microlensing transients. Their rate is an internal
  pipeline diagnostic only.
- The parallax utility consumes observer coordinates in an inertial frame, but
  has not been cross-validated against an independent microlensing package for
  the supplied barycentric ephemeris. It is excluded from default claims.
- Earlier outputs used truth-seeded fitting and obsolete cadence assumptions.
  They are retained for provenance but are scientifically superseded.
