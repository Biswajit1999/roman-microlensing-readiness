# Contributing

Bug reports, replication attempts, and scientific critique are welcome via
GitHub Issues and Discussions.

## Development setup

```bash
git clone https://github.com/Biswajit1999/roman-microlensing-readiness.git
cd roman-microlensing-readiness
python -m pip install -e ".[dev]"
pytest -q            # fast tests (< 1 minute)
pytest -q -m slow     # adds the ray-shooting binary-lens validation tests
```

## Before opening a pull request

- Run `pytest -q` and `pytest -q -m slow`; both must pass.
- Run `ruff check src tests`.
- If you change a physical model, add or update a test that checks it
  against a hand calculation or a known analytic limit (see
  `tests/test_pspl.py`, `tests/test_fspl.py`, `tests/test_planetary.py` for
  the existing pattern), and update `docs/VALIDATION.md`.
- If you change a scientific claim or default parameter, update
  `docs/CLAIMS.md` and `docs/LIMITATIONS.md` accordingly.
- Keep commits small and focused on one logical change.

## Good first issues

See the repository Issues tab for labeled starter tasks, including
documentation gaps, additional validation tests, and known limitations
listed in `docs/LIMITATIONS.md` that are open for contribution (e.g. an
analytic closed-form finite-source cross-check, or a VBMicrolensing-based
cross-validation of the binary-lens ray-shooting magnification).
