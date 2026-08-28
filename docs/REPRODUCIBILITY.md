# Reproducibility

## Environment

```bash
git clone https://github.com/Biswajit1999/roman-microlensing-readiness.git
cd roman-microlensing-readiness
python -m pip install -e ".[dev]"   # requires Python >= 3.10
```

Pinned minimum versions are declared in `pyproject.toml`
(`numpy>=1.24`, `scipy>=1.10`, `pandas>=2.0`, `matplotlib>=3.7`,
`pyyaml>=6.0`, `click>=8.1`). Development was verified against Python 3.12.10
and 3.9.19 (see `docs/VALIDATION.md`); CI (`.github/workflows/ci.yml`) pins
exact CI-runner versions.

## One-command reproduction of a full result

```bash
romanmlr fetch-data --cache-dir data/cache
romanmlr run-grid --config configs/default.yaml --out results/default
romanmlr null-fpr --config configs/default.yaml --out results/default
```

This regenerates `results/default/trials.csv`, `results/default/completeness.csv`,
and `results/default/false_positive_rate.json` from scratch. A smaller,
seconds-scale smoke test is available via `configs/smoke_test.yaml` and is
run in CI on every push.

## Determinism

- Every `TrialConfig` carries its own `seed`; `cadence.generate_observation_times`
  and `noise.add_noise` are deterministic given that seed
  (`numpy.random.default_rng(seed)`), verified in
  `tests/test_cadence.py::test_deterministic_given_seed`.
- The binary-lens ray-shooting grid (`planetary.build_ray_shot_tree`) is a
  fixed deterministic grid, not a random sample, so it is exactly
  reproducible given the same `BinaryLensConfig`.
- Downloaded external data is checksummed on first fetch
  (`data/cache/manifest.json`, SHA-256) so any future drift in the upstream
  Data Challenge repository would change the checksum, not silently change
  results.

## What is *not* committed

Per the project-wide convention (see the top-level programme specification),
large raw data (`lc.tar.gz`, ~100 MB) and the local download cache
(`data/cache/`) are git-ignored and fetched on demand; only small, real
excerpts used as offline test fixtures are committed (`tests/test_data_adapter.py`).
