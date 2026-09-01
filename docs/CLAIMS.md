# Claims ledger

| Claim | Evidence | Status |
|---|---|---|
| Point-source point-lens magnification matches the analytic formula. | `tests/test_pspl.py` | Unit verified |
| Uniform-source finite-source magnification approaches point-source behavior away from the source. | `tests/test_fspl.py` | Unit verified in tested limit |
| A blind search can recover a high-S/N synthetic event without truth-seeded parameters. | `tests/test_detect.py::test_blind_search_recovers_without_truth_seed` | Unit verified |
| Event detection and parameter recovery are stored separately. | `src/romanmlr/injection_recovery.py`, tests | Verified by software tests |
| The default cadence is an official final/as-flown Roman schedule. | None | Rejected; versioned proxy only |
| The custom binary-lens solver supports scientific planetary inference. | Non-convergent reference limit | Rejected; runtime-disabled |
| Earlier 58% recovery and 0/200 false-positive values describe the post-audit pipeline. | Earlier, truth-seeded outputs | Superseded |
| A post-audit Roman completeness, readiness, yield, or survey false-positive rate is established. | None | Not claimed |

Any future numerical statement must name its raw CSV/JSON, copied config,
manifest, numerator/denominator, selection rule, and interval. A simple
synthetic-null rate must be labelled as such, never “Roman FPR.”
