# Reproducibility

## Environment and verification

```bash
git clone https://github.com/Biswajit1999/roman-microlensing-readiness.git
cd roman-microlensing-readiness
python -m pip install -e ".[dev]"
pytest -q
ruff check src tests scripts
```

The v0.5 release was verified with 39 passing tests (one network test excluded
by default) on Python 3.12. CI also tests Python 3.10 and 3.12, lints the source,
and runs the CLI smoke workflow.

## Recreate the v0.5 experiment

```bash
romanmlr run-grid \
  --config configs/cadence_phase_v0.5.yaml \
  --out results/v0.5.0-release

romanmlr null-fpr \
  --config configs/cadence_phase_v0.5.yaml \
  --out results/v0.5.0-null \
  --n-trials 1000

python scripts/build_v0_5_evidence.py \
  --trials results/v0.5.0-release/trials.csv \
  --null-trials results/v0.5.0-null/null_trials.csv \
  --null-summary results/v0.5.0-null/null_summary.json \
  --out research
```

On the recorded Windows host, the 900-trial run had a median per-trial time of
0.228 s, a 99th percentile of 29.9 s, and a 41.4 s maximum. The distribution
is strongly right-skewed, so allow about 25 minutes for a serial replay. The
null run is separate and can run concurrently on another core.

## Outputs and integrity

The injection directory contains:

- `trials.csv`: one raw row per injection, including all master/child seeds;
- `conditional_recovery.csv`: backward-compatible detection endpoint table;
- `recovery_by_endpoint.csv`: detection and parameter endpoints kept separate;
- `run_summary.json`: overall numerators, denominators, intervals, failures;
- `config.yaml` and `manifest.json`: exact inputs and execution provenance.

The null directory contains every searched realization in `null_trials.csv`,
its `null_summary.json`, copied config, and manifest. Both manifests record
clean source commit `4dfb89f01df8877e32b2f3af0437505167418b3d`, the same
config SHA-256, runtime, dependency versions, and RNG declaration.

`research/result_summary.json` records SHA-256 digests of the two primary input
artifacts. The evidence script derives every CSV and SVG; no plotted value is
typed into a figure by hand.

Do not overwrite a run directory during a replication attempt. Use a new path,
compare all scientific columns, and expect `wall_time_s` to differ. A clean
pre-release replay matched all 900 scientific rows bit-for-bit; only wall time
changed.

`configs/planetary.yaml` is deliberately disabled and the CLI rejects it. This
is a reproducible safety property, not an unfinished documentation note.
