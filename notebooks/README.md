# notebooks/

`roman_microlensing_readiness_colab.ipynb` is a thin, Colab-ready
walkthrough backed entirely by `romanmlr` package functions (no
copy-pasted analysis code). It:

1. Installs the package directly from GitHub (`pip install git+...`).
2. Runs the exact-limit validation checks from `tests/test_pspl.py` and
   `tests/test_fspl.py` inline, so a reader can see the physics checks
   pass without trusting the README.
3. Runs a fast injection-recovery grid (equivalent to
   `configs/smoke_test.yaml`) end to end on the free Colab CPU runtime,
   typically well under two minutes.
4. Plots a completeness curve with its Wilson-score confidence band.
5. Ends with the same limitations summary as `docs/LIMITATIONS.md`.

No credentials are required for the default demonstration path. Fixing a
seed makes the run reproducible; package/dependency versions are printed at
the top of the notebook.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Biswajit1999/roman-microlensing-readiness/blob/main/notebooks/roman_microlensing_readiness_colab.ipynb)
