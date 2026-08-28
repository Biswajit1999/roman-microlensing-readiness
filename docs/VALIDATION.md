# Validation

Every physical model in this repository is checked against at least one
independent, analytically known quantity -- never only against itself.
This file summarizes what was checked, how, and the result; the
authoritative, re-runnable checks are the pytest suite referenced below.

| Model | Check | Method | Test | Result (2026-08-28) |
|---|---|---|---|---|
| PSPL magnification | Hand calculation at u=0.5, 1.0 | Direct arithmetic | `tests/test_pspl.py::test_magnification_hand_calculation` | Exact match to float precision |
| PSPL magnification | Asymptotic limits (u->inf gives A->1; u->0 diverges; monotonic) | Analytic limits | `tests/test_pspl.py::test_magnification_limits` | Pass |
| PSPL + parallax | piE -> 0 limit reduces to the unperturbed trajectory | Analytic limit, three shrinking |piE| values | `tests/test_pspl.py::test_parallax_vanishes_as_pie_shrinks` | Deviation shrinks monotonically, <1e-3 at piE=1e-4 |
| FSPL | u >> rho reduces to point-lens magnification | Analytic limit | `tests/test_fspl.py::test_fspl_converges_to_point_lens_away_from_source` | Agreement to 0.2% |
| FSPL | Finite (non-divergent) magnification at u=0 | Analytic expectation (disk averaging removes the point-lens singularity) | `tests/test_fspl.py::test_fspl_finite_at_u_equal_zero` | Finite, as expected |
| Binary lens (ray shooting) | q -> 0 reduces to the single-lens finite-source magnification | Analytic limit, q=1e-6 | `tests/test_planetary.py::test_vanishing_mass_ratio_matches_single_lens` | Agreement to 8% (Monte-Carlo-scale tolerance; see `docs/LIMITATIONS.md`) |
| Binary lens (ray shooting) | s >> 1 (wide separation) reduces to the primary-alone point-lens magnification | Analytic limit, s=8 | `tests/test_planetary.py::test_wide_separation_matches_two_decoupled_lenses` | Agreement to 10% |
| Cadence generator | Deterministic given seed; respects season gaps; dropout reduces point count | Direct construction | `tests/test_cadence.py` | Pass |
| PSPL fit | Recovers injected (t0, u0, tE) from a synthetic high-SNR light curve | Synthetic recovery | `tests/test_detect.py::test_fit_recovers_injected_parameters` | tE within 10%, u0 within 0.02, t0 within 1 day |
| Detection statistic | High-SNR injected event exceeds threshold; pure Gaussian noise does not | Synthetic null + signal test | `tests/test_detect.py::test_event_detected_well_above_threshold`, `test_pure_noise_does_not_trigger_detection` | Pass |
| Anomaly statistic | An injected localized flux deviation is flagged; the same light curve without it is not | Synthetic null + signal test | `tests/test_detect.py::test_anomaly_chi2_flags_injected_deviation` | Pass |
| Wilson-score interval | k=0, k=n, k=n/2 edge cases; interval narrows with more trials | Hand-verified statistics | `tests/test_completeness.py` | Pass |
| Data adapter (`event_info.txt`, `master_file.txt` parser) | Parses real, verbatim excerpts of the public Data Challenge answer key correctly, including all four event classes | Fixture built from real upstream data | `tests/test_data_adapter.py` | Pass |
| Data adapter (full dataset) | Full 293-row `Answers/master_file.txt` parses to exactly the published per-class counts (74/83/43/93) | Manual one-off run against the live upstream file, 2026-08-28 | not yet wired into CI as an automated network test beyond `test_real_download_and_manifest` | 293/293 rows parsed; class counts 74 (dcnormffp), 83 (ombin), 43 (omcassan), 93 (dccv) match Penny et al.'s published dataset description exactly |
| End-to-end pipeline | CLI `run-grid` on `configs/smoke_test.yaml` produces physically sensible trends (higher tE / smaller u0 -> higher recovered delta-chi2; an in-season vs. in-gap `t0` changes `n_points_in_anomaly_window` as expected) | Manual run, 2026-08-28 | `configs/smoke_test.yaml` | Confirmed by inspection of `results/smoke/trials.csv` during development; see git history |

## Open validation failure: bound-planet-channel population grid (2026-08-28)

Attempting to run a bound-planet-channel injection-recovery grid
(`configs/planetary.yaml`) surfaced a real, unresolved bug: at q=0.0001
(negligible planet), `magnification_binary_track` disagrees with the
exact point-lens formula by up to ~0.8-1.0 in magnification at some
trajectory points, and **this does not shrink with finer ray-shooting
resolution** (max|diff| = 0.78, 0.94, 0.99 at grid_n = 350, 700, 1400 --
flat-to-growing). This was caught specifically because the fitted
single-lens model, evaluated against the *actual* injected flux, gave
chi2/n = 1.00 (a perfect fit) while the same fit evaluated against the
*exact analytic* PSPL formula gave chi2/n = 4.37 -- proving the
discrepancy is in the ray-shooting magnification itself, not the
fit/noise/detection code (all of which check out as correct via this same
diagnostic). Two related, real bugs were found and fixed in the same
investigation:

1. **Ray-shooting undersampling could silently invert the result.** The
   original `configs/planetary.yaml` used `rho=0.005` with `grid_n=250`,
   giving an image-plane cell size (~0.024) *larger* than the source disk
   -- a regime `planetary.py`'s validated tests never exercised. This
   produced a spuriously large (~3x) magnification spike near peak
   brightness. Fixed by adding a runtime guard in
   `build_ray_shot_tree` that raises `ValueError` instead of silently
   returning an unreliable number when `cell_size > rho`
   (`tests/test_planetary.py::test_undersampled_grid_raises_instead_of_silently_returning_bad_values`).
2. **Unconstrained fs/fb bounds let the single-lens fit run away to a
   degenerate solution** (e.g. fs=146, fb=-145, nearly cancelling) for
   some high-magnification configurations, reported as "success" by the
   optimizer despite being clearly wrong. Fixed by tightening the fs/fb
   fit bounds to [-2, 5] (documented as safe specifically because every
   synthetic light curve in this project uses fs=1, fb=0; see
   `detect.py`).

Both fixes are real and are included in this release. The **third,
deeper issue** (the non-shrinking-with-resolution discrepancy itself) is
**not fixed** -- root cause not yet identified. See
`docs/LIMITATIONS.md` for the full writeup and the pinned GitHub issue.
No bound-planet-channel population result is published in this release
because of this open issue.

## Explicitly not yet validated

- The root cause of the non-shrinking ray-shooting discrepancy above
  (pinned, high-priority repository issue).
- No cross-check yet against an independently implemented microlensing
  package (`pyLIMA`, `MulensModel`, `VBMicrolensing`) on a shared test
  event. This is now an even higher-priority validation step given the
  finding above, and is tracked as a repository issue.
- No comparison of recovered completeness against a previously published
  Roman/WFIRST injection-recovery study's numbers (e.g. Penny et al. 2019
  Figure values) at matched parameters -- the cadence and noise models here
  are independent implementations, so exact agreement is not expected, but
  qualitative agreement (e.g. relative sensitivity to tE, u0) is a
  reasonable target for a follow-up validation pass.

## Reproducing these checks

```bash
pytest -q                 # fast checks (< 10 s)
pytest -q -m slow          # ray-shooting binary-lens limit checks (< 5 s)
pytest -q -m network       # live download + full-dataset parse (requires internet)
```
