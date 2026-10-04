# results/

Generated output only -- every file here is reproducible from
`configs/*.yaml` via `romanmlr run-grid` / `romanmlr null-fpr`
(see `docs/REPRODUCIBILITY.md`). Nothing in this directory is hand-edited.

- `post_audit_smoke/`, `post_audit_null_smoke/` -- v0.4 software checks, not
  scientific results.
- `v0.5.0-release/` -- clean-commit 900-injection blind recovery experiment.
- `v0.5.0-null/` -- 1,000 constant-flux realizations searched identically.
- `figures/recovery-vs-timescale-v0.5.svg` -- generated primary result figure.
- `default/` -- historical v0.2 truth-seeded output, scientifically superseded
  and retained only for provenance.
