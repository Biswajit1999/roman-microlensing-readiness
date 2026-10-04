"""Build the versioned v0.5 numerical summaries and SVG evidence figures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from romanmlr.completeness import recovery_by_endpoint, wilson_interval

def _sha256(path: Path) -> str:
    # Git can materialize text files with CRLF or LF depending on checkout
    # settings. Hash canonical LF bytes so provenance checks are portable.
    canonical = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(canonical).hexdigest()


def _endpoint_summary(frame: pd.DataFrame, column: str) -> dict:
    n = len(frame)
    k = int(frame[column].sum())
    point, low, high = wilson_interval(k, n)
    return {"n": n, "k": k, "fraction": point, "ci_low": low, "ci_high": high}


def _sampling_class(values: pd.Series) -> pd.Categorical:
    return pd.cut(
        values,
        bins=[-np.inf, 2, 9, 29, np.inf],
        labels=["<3", "3-9", "10-29", ">=30"],
        ordered=True,
    )


def _edge_class(values: pd.Series) -> pd.Categorical:
    return pd.cut(
        values,
        bins=[-np.inf, 1, 3, np.inf],
        labels=["<1 tE", "1-3 tE", ">=3 tE"],
        ordered=True,
    )


def _save_svg(fig: plt.Figure, output: Path) -> None:
    """Write deterministic, diff-clean SVG output."""
    fig.savefig(output, format="svg", metadata={"Date": None})
    lines = output.read_text(encoding="utf-8").splitlines()
    output.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def _write_recovery_figure(table: pd.DataFrame, output: Path) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "romanmlr-v0.5",
    })
    colors = {19.0: "#2364aa", 22.0: "#7b2cbf", 24.0: "#c44536"}
    markers = {"event_detected": "o", "parameters_recovered": "s"}
    labels = {"event_detected": "detected", "parameters_recovered": "parameters recovered"}
    fig, ax = plt.subplots(figsize=(10.4, 6.2), constrained_layout=True)
    for magnitude in sorted(table["mag_ref"].unique()):
        for endpoint, marker in markers.items():
            subset = table[(table["mag_ref"] == magnitude) & (table["endpoint"] == endpoint)]
            subset = subset.sort_values("tE")
            yerr = np.vstack(
                (subset["completeness"] - subset["ci_low"], subset["ci_high"] - subset["completeness"])
            )
            ax.errorbar(
                subset["tE"], subset["completeness"], yerr=yerr,
                color=colors[magnitude], marker=marker, linewidth=2.0,
                capsize=3, linestyle="-" if endpoint == "event_detected" else "--",
                label=f"F146={magnitude:g}, {labels[endpoint]}",
            )
    ax.set_xscale("log")
    ax.set_xticks(sorted(table["tE"].unique()))
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("Injected Einstein crossing time, tE (days)")
    ax.set_ylabel("Conditional recovery fraction (Wilson 95% CI)")
    ax.set_title("Blind detection and parameter identifiability under the v0.5 proxy")
    ax.grid(axis="y", color="#d7dce2", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=2, fontsize=8.5, frameon=False, loc="lower right")
    fig.text(
        0.01, 0.005,
        "Synthetic isolated point lenses; 75 injections per (magnitude, tE) cell after pooling u0. "
        "Not a Roman yield or mission-completeness forecast.",
        fontsize=8, color="#4a5560",
    )
    _save_svg(fig, output)
    plt.close(fig)


def build(
    trials_path: Path,
    null_trials_path: Path,
    null_summary_path: Path,
    output: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    figures = output.parent / "results" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    trials = pd.read_csv(trials_path)
    null_trials = pd.read_csv(null_trials_path)
    null_summary = json.loads(null_summary_path.read_text())
    if len(null_trials) != null_summary["n_trials"]:
        raise ValueError("null trial count does not match null summary")
    if int(null_trials["event_detected"].sum()) != null_summary["n_false_positive"]:
        raise ValueError("null trigger count does not match null summary")

    primary = recovery_by_endpoint(trials, ["mag_ref", "tE"])
    primary.to_csv(output / "recovery_by_magnitude_timescale.csv", index=False)

    trials = trials.copy()
    trials["sampling_class"] = _sampling_class(trials["n_epochs_within_tE"])
    sampling = recovery_by_endpoint(trials, ["sampling_class"])
    sampling.to_csv(output / "recovery_by_sampling.csv", index=False)
    trials["season_edge_class"] = _edge_class(trials["season_edge_distance_tE"])
    edges = recovery_by_endpoint(trials, ["season_edge_class"])
    edges.to_csv(output / "recovery_by_season_edge.csv", index=False)

    detected = trials[trials["event_detected"]]
    conditional = _endpoint_summary(detected, "parameters_recovered") if len(detected) else None
    summary = {
        "scope": "conditional synthetic point-lens recovery; not mission completeness or yield",
        "input_sha256": {
            str(trials_path.as_posix()): _sha256(trials_path),
            str(null_trials_path.as_posix()): _sha256(null_trials_path),
            str(null_summary_path.as_posix()): _sha256(null_summary_path),
        },
        "n_injections": len(trials),
        "event_detection": _endpoint_summary(trials, "event_detected"),
        "parameter_recovery": _endpoint_summary(trials, "parameters_recovered"),
        "parameter_recovery_given_detection": conditional,
        "fit_failures": int((~trials["fit_success"]).sum()),
        "unique_master_seeds": int(trials["seed"].nunique()),
        "null_test": null_summary,
    }
    (output / "result_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    _write_recovery_figure(primary, figures / "recovery-vs-timescale-v0.5.svg")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=Path, required=True)
    parser.add_argument("--null-trials", type=Path, required=True)
    parser.add_argument("--null-summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("research"))
    args = parser.parse_args()
    build(args.trials, args.null_trials, args.null_summary, args.out)


if __name__ == "__main__":
    main()
