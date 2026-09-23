import json

import pandas as pd
from click.testing import CliRunner

from romanmlr.cli import _stable_trial_seed, main


def test_parameter_aware_seed_is_stable_and_distinct():
    first = _stable_trial_seed("experiment", {"u0": 0.1}, 0)
    assert first == _stable_trial_seed("experiment", {"u0": 0.1}, 0)
    assert first != _stable_trial_seed("experiment", {"u0": 0.2}, 0)
    assert first != _stable_trial_seed("experiment", {"u0": 0.1}, 1)


def test_run_grid_writes_endpoint_and_provenance_outputs(tmp_path):
    result = CliRunner().invoke(
        main,
        [
            "run-grid",
            "--config",
            "configs/smoke_test.yaml",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    trials = pd.read_csv(tmp_path / "trials.csv")
    endpoints = pd.read_csv(tmp_path / "recovery_by_endpoint.csv")
    summary = json.loads((tmp_path / "run_summary.json").read_text())
    assert trials["seed"].is_unique
    assert set(endpoints["endpoint"]) == {"event_detected", "parameters_recovered"}
    assert summary["n_trials"] == len(trials)
    assert (tmp_path / "manifest.json").is_file()
