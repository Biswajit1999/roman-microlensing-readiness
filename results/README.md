# results/

Generated output only -- every file here is reproducible from
`configs/*.yaml` via `romanmlr run-grid` / `romanmlr null-fpr`
(see `docs/REPRODUCIBILITY.md`). Nothing in this directory is hand-edited.

- `smoke/` -- output of `configs/smoke_test.yaml`, a seconds-scale sanity
  check (not a scientific result), regenerated in CI.
- `default/` -- output of `configs/default.yaml`, the primary experiment
  (added once a full run has been generated and reviewed; see
  `PORTFOLIO_PROGRESS.md` for status).
