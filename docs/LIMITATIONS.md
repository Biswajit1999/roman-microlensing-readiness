# Limitations and Known Failure Modes

This file is maintained honestly and is expected to grow. A short list here
is a sign of insufficient testing, not a sign of a finished project.

## Binary-lens (planetary channel) solver

- **Open, unresolved issue (found 2026-08-28, not yet fixed): a
  non-shrinking discrepancy from the exact point-lens limit.** Attempting
  a bound-planet population injection-recovery grid surfaced a real bug:
  even at q=0.0001 (a negligible planet, which should reduce almost
  exactly to the finite-source point-lens result), `magnification_binary_track`
  disagrees with the exact point-lens formula by up to ~0.8-1.0 in
  magnification at some points along a typical trajectory. Critically,
  this discrepancy does **not** shrink with finer sampling: max|diff| was
  0.78, 0.94, and 0.99 at `grid_n` = 350, 700, and 1400 respectively --
  flat-to-growing, not the O(1/sqrt(N)) shrinkage expected of a pure
  ray-density sampling-noise effect. This means the discrepancy is a real
  algorithmic bug, not (only) an undersampling artifact, and it is **not
  fixed by increasing grid_n**. Root cause not yet identified. Until this
  is resolved, **no bound-planet-channel injection-recovery result from
  this project should be treated as valid** -- `configs/planetary.yaml`
  and any grid run from it are explicitly withheld from `results/` for
  exactly this reason (see the config's own header). Tracked as a
  pinned, high-priority repository issue.
- Separately, and more routinely: `planetary.magnification_binary_track`
  uses inverse ray shooting, not a closed-form/exact solver, and has an
  inherent per-call, Monte-Carlo-like scatter that *does* shrink with
  `grid_n` in the two narrower, specific configurations validated in
  `tests/test_planetary.py` (vanishing mass ratio at fixed beta=0.1;
  wide separation at two fixed trajectory points) -- ~5-10% agreement
  there, not sub-percent precision. That validated, shrinking-with-
  resolution scatter is a separate, expected limitation from the
  non-shrinking discrepancy described above, which was only found by
  sweeping many more trajectory points than those two tests cover. Do not
  use this module for a precision retrieval of a real candidate event.
- When zero rays land inside the (typically small) source disk for a given
  trajectory point -- a finite-ray-density undersampling artifact, not a
  physical demagnification-to-zero -- the code floors the magnification at
  the primary-alone point-lens value (`planetary.py`, see inline comment).
  This floor is a documented approximation, most conservative (i.e. most
  likely to *understate* the true local magnification) very close to the
  planetary caustic itself, exactly where planetary detections are most
  interesting. A future contribution should replace this with adaptive
  mesh refinement or a validated closed-form solver
  (e.g. cross-check against VBMicrolensing).
- The anomaly-detection window for the planetary channel
  (`injection_recovery._anomaly_window_mask`) is a simple heuristic (a fixed
  window around the time the trajectory passes the companion's projected
  separation), not a caustic-topology-aware window. It will under- or
  over-estimate the true perturbation duration for resonant (s ~ 1)
  configurations where the caustic structure is more complex than the
  wide/close approximation implicitly assumes.

## Finite-source model

- `fspl.magnification_fspl` assumes a **uniform-brightness** source disk.
  Limb darkening is not modeled, which matters most for giant/subgiant
  source stars during caustic crossings. This is a documented
  simplification, not an oversight; adding a linear-limb-darkening kernel
  to the disk integral is a natural, scoped follow-up (tracked as a
  repository issue).

## Noise model

- `noise.py`'s photometric-uncertainty model is a simple two-term
  (Poisson-like + floor) magnitude-dependent model calibrated qualitatively
  to be of the right order for W149-band Roman-like photometry, not a
  derived instrument exposure-time calculator. The AR(1) correlated-noise
  term is a generic red-noise proxy, not a physically derived model of any
  specific systematic (e.g. differential velocity aberration, detector
  persistence, or background variation).

## Cadence model

- `cadence.py` defaults (6 x 72-day seasons, 15-minute cadence) follow the
  Penny et al. (2019) community-design reference, not the final as-flown
  Roman GBTDS observing plan, which is set by the Roman project and may
  differ (see `docs/DATA_SOURCES.md`). All cadence parameters are exposed
  as configuration precisely so results can be regenerated once the final
  design (or an official simulated dataset built on it, e.g. RMDC26) is
  available.

## Detection statistics

- `detect.fit_pspl` is a single, bounded nonlinear least-squares fit from
  one initial guess; it is not a global optimizer or a Markov-Chain Monte
  Carlo sampler, and can converge to a local minimum for low-SNR or
  strongly blended events. Injection-recovery statistics computed here
  should be read as "recoverable by a straightforward single-lens fit,"
  not as an upper bound achievable by more sophisticated pipelines (e.g.
  multi-start optimization, MCMC, or the full modeling stacks used in
  real microlensing surveys).
- The event and anomaly delta-chi2 thresholds (500 and 160 respectively)
  are literature-typical defaults, not values tuned or validated
  specifically for this project's noise model; both are exposed as
  configuration for exactly this reason (see `docs/METHODS.md`).

## Scope not covered by v0.1

- No orbital-motion or higher-order (xallarap, finite-lens) effects.
- No multi-band (W149/Z087 joint) fitting; the pipeline is single-band.
- No comparison against a second, independently implemented baseline
  (e.g. `pyLIMA` or `MulensModel`) yet -- tracked as a repository issue for
  external cross-validation.
