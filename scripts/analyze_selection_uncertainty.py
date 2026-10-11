"""Generate threshold, dropout, and injection-count sensitivity evidence."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from romanmlr.selection_uncertainty import (
    cadence_dropout_retention,
    injection_count_plan,
    threshold_operating_curve,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    injections = pd.read_csv(root / "results/v0.5.0-release/trials.csv")
    null_trials = pd.read_csv(root / "results/v0.5.0-null/null_trials.csv")
    thresholds = (10, 20, 25, 30, 40, 100, 250, 500, 1000, 2000)
    operating = threshold_operating_curve(injections, null_trials, thresholds)
    dropout = cadence_dropout_retention(injections, (0, 0.05, 0.10, 0.20, 0.35, 0.50))
    planning = injection_count_plan()

    research = root / "research"
    operating.to_csv(research / "threshold_operating_curve.csv", index=False)
    dropout.to_csv(research / "cadence_dropout_retention.csv", index=False)
    planning.to_csv(research / "injection_count_plan.csv", index=False)
    summary = {
        "schema": "romanmlr-selection-uncertainty/1",
        "scope": "sensitivity of the committed balanced synthetic v0.5 software experiment",
        "is_roman_population_forecast": False,
        "threshold_rows": operating.to_dict(orient="records"),
        "dropout_rows": dropout.to_dict(orient="records"),
        "planning_rows": planning.to_dict(orient="records"),
    }
    (research / "selection_uncertainty.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    axes[0].semilogx(
        operating["threshold_delta_chi2"],
        operating["conditional_detection_fraction"],
        marker="o",
        label="Injected point lenses",
    )
    axes[0].semilogx(
        operating["threshold_delta_chi2"],
        operating["simple_null_fpr"],
        marker="o",
        label="Gaussian constant-flux null",
    )
    axes[0].set(
        xlabel="Blind-search threshold (delta chi-square)",
        ylabel="Conditional fraction",
        ylim=(-0.03, 1.03),
        title="Threshold sensitivity",
    )
    axes[0].legend(fontsize=8)
    axes[1].plot(
        100 * dropout["dropout_fraction"],
        dropout["mean_retention_probability"],
        marker="o",
        color="#7c3aed",
    )
    axes[1].set(
        xlabel="Independent epoch dropout (%)",
        ylabel="Mean P(retain at least 3 epochs within tE)",
        ylim=(0, 1.03),
        title="Cadence-support thinning",
    )
    figure.suptitle(
        "Balanced synthetic v0.5 experiment — not Roman population completeness", fontsize=11
    )
    figure.savefig(root / "results/figures/selection-uncertainty.png", dpi=170)
    plt.close(figure)
    print(
        json.dumps(
            {
                "threshold_500": operating.loc[
                    operating.threshold_delta_chi2 == 500
                ].iloc[0].to_dict(),
                "dropout_50pct": dropout.iloc[-1].to_dict(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
