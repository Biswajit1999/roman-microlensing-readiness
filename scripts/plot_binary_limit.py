"""Regenerate the q->0 / phase-sensitivity diagnostic plot."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    ns = [int(x) for x in data["results"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    for q in ("1e-06", "0.0001"):
        errors = [data["results"][str(n)]["production_solver"][q]["max_absolute_error"]
                  for n in ns]
        ax.plot(ns, errors, "o-", label=f"Existing solver q={q}")
    for phase in (0.0, 0.5):
        errors = []
        for n in ns:
            rows = data["results"][str(n)]["independent_grid"]
            errors.append(next(r["max_absolute_error"] for r in rows
                               if r["q"] == 0 and r["phase"] == phase))
        ax.plot(ns, errors, "s--", label=f"Independent q=0, phase={phase}")
    ax.set_xlabel("Image-plane rays per side")
    ax.set_ylabel("Maximum absolute magnification residual")
    ax.set_title("Synthetic point-lens limit audit — NOT validated planetary science")
    ax.legend(fontsize=8)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
