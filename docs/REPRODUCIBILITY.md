# Reproducibility

```bash
git clone https://github.com/Biswajit1999/roman-microlensing-readiness.git
cd roman-microlensing-readiness
python -m pip install -e ".[dev]"
pytest -q

romanmlr run-grid --config configs/smoke_test.yaml --out results/post_audit_smoke
romanmlr null-fpr --config configs/smoke_test.yaml --out results/post_audit_null --n-trials 50
```

The grid writes `trials.csv`, `conditional_recovery.csv`, `config.yaml`, and
`manifest.json`. The null run writes every searched realization to
`null_trials.csv`, plus `null_summary.json`, the config, and manifest. Null and
injection searches use the same blind event finder.

`configs/default.yaml` defines the larger exploratory grid. Do not overwrite a
run directory. Use a new version-labelled path and review raw fit parameters,
failed fits, selection counts, confidence intervals, and the manifest before
quoting any aggregate.

`configs/planetary.yaml` is deliberately disabled and the CLI will reject it.
This is a reproducible safety property, not an unfinished documentation note.
