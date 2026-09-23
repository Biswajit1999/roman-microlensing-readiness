import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRIALS = ROOT / "results" / "v0.5.0-release" / "trials.csv"
NULL_TRIALS = ROOT / "results" / "v0.5.0-null" / "null_trials.csv"


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_numerators_trace_to_raw_rows():
    trials = pd.read_csv(TRIALS)
    summary = _json(ROOT / "results" / "v0.5.0-release" / "run_summary.json")
    assert len(trials) == summary["n_trials"] == 900
    assert int(trials["event_detected"].sum()) == summary["event_detected"]["n_success"] == 864
    assert int(trials["parameters_recovered"].sum()) == 710
    assert int((~trials["fit_success"]).sum()) == summary["n_fit_failures"] == 11


def test_release_random_streams_are_unique():
    trials = pd.read_csv(TRIALS)
    for column in ("seed", "cadence_seed", "epoch_seed", "noise_seed"):
        assert trials[column].nunique() == len(trials)


def test_null_summary_and_evidence_hashes_trace_to_raw_inputs():
    null_trials = pd.read_csv(NULL_TRIALS)
    null_summary = _json(ROOT / "results" / "v0.5.0-null" / "null_summary.json")
    evidence = _json(ROOT / "research" / "result_summary.json")
    assert len(null_trials) == null_summary["n_trials"] == 1000
    assert int(null_trials["event_detected"].sum()) == null_summary["n_false_positive"] == 0
    hashes = evidence["input_sha256"]
    assert hashes["results/v0.5.0-release/trials.csv"] == _sha256(TRIALS)
    assert hashes["results/v0.5.0-null/null_trials.csv"] == _sha256(NULL_TRIALS)


def test_release_manifests_record_clean_identical_source_commit():
    injection = _json(ROOT / "results" / "v0.5.0-release" / "manifest.json")
    null = _json(ROOT / "results" / "v0.5.0-null" / "manifest.json")
    assert injection["git_dirty"] is False
    assert null["git_dirty"] is False
    assert injection["git_commit"] == null["git_commit"]
    assert injection["config_sha256"] == null["config_sha256"]
