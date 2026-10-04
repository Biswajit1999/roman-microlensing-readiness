# Claims ledger

Every quantitative claim names a committed test or generated evidence file.
The word “completeness” is intentionally avoided for the v0.5 headline because
the grid is balanced, conditional, and not population weighted.

| # | Claim | Evidence | Status |
|---|---|---|---|
| 1 | Point-source point-lens magnification matches the analytic formula in tested cases. | `tests/test_pspl.py` | Unit verified |
| 2 | Uniform-source finite-source magnification approaches point-source behaviour away from the source. | `tests/test_fspl.py` | Unit verified in tested limit |
| 3 | The blind search can recover a high-S/N event without injected parameters. | `tests/test_detect.py::test_blind_search_recovers_without_truth_seed` | Unit verified |
| 4 | v0.5 assigns a unique parameter-aware master seed to every grid trial and separates cadence, epoch, and noise streams. | `tests/test_cli.py`, `tests/test_injection_recovery.py`, `results/v0.5.0-release/trials.csv` | Verified; 900/900 unique in each stream |
| 5 | The 900-injection balanced grid detects 864 events: 96.0%, Wilson 95% CI 94.5–97.1%. | `research/result_summary.json` | Conditional software result |
| 6 | The same grid recovers the predeclared parameters in 710 events: 78.9%, CI 76.1–81.4%; among detections the fraction is 82.2%, CI 79.5–84.6%. | `research/result_summary.json` | Conditional software result |
| 7 | At F146=24 and tE=0.02 d, 41/75 are detected (54.7%, CI 43.4–65.4%) and 22/75 recover parameters (29.3%, CI 20.2–40.4%). | `research/recovery_by_magnitude_timescale.csv` | Predeclared subgroup result |
| 8 | Parameter recovery is associated with cadence support: 134/225 (59.6%) with 3–9 epochs within one tE versus 409/450 (90.9%) with at least 30. | `research/recovery_by_sampling.csv` | Descriptive association; not causal |
| 9 | The identical blind search triggers on 0/1,000 simple constant-flux nulls; the Wilson 95% upper bound is 0.383%. | `results/v0.5.0-null/null_summary.json` | Internal null diagnostic only |
| 10 | The v0.5 release evidence was generated from clean commit `4dfb89f` with config SHA-256 `5d8d3f…c6bf`. | both v0.5 manifests | Provenance verified |
| 11 | The current cadence is an official final or as-flown Roman schedule. | None | Rejected; versioned proxy only |
| 12 | The custom binary-lens solver supports scientific planetary inference. | Failed convergence limit and runtime guard | Rejected; pathway disabled |
| 13 | v0.5 establishes Roman population completeness, readiness, yield, or survey false-positive rate. | None | Not claimed |
| 14 | Earlier 58% recovery and 0/200 values describe the blind v0.5 pipeline. | Historical truth-seeded outputs | Superseded |
