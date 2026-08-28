"""Command-line workflow for the Roman Microlensing Readiness Benchmark."""
from __future__ import annotations

import json
from pathlib import Path

import click
import yaml

from .cadence import CadenceConfig
from .completeness import completeness_by_bin, false_positive_rate
from .data import MDCPaths, load_event_info, load_master_truth
from .injection_recovery import TrialConfig, run_grid


@click.group()
def main() -> None:
    """romanmlr: Roman GBTDS microlensing injection-recovery benchmark."""


@main.command("fetch-data")
@click.option("--cache-dir", default="data/cache", show_default=True)
def fetch_data(cache_dir: str) -> None:
    """Download and cache the public 2018 WFIRST Microlensing Data Challenge
    ground-truth tables (event_info.txt, Answers/master_file.txt)."""
    paths = MDCPaths(cache_dir=Path(cache_dir))
    info = load_event_info(paths)
    truth = load_master_truth(paths)
    click.echo(f"event_info: {len(info)} rows -> {paths.cache_dir/'event_info.txt'}")
    click.echo(f"master_truth: {len(truth)} rows -> {paths.cache_dir/'master_file.txt'}")
    click.echo(f"provenance manifest: {paths.manifest}")


@main.command("run-grid")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", default="results", show_default=True)
def run_grid_cmd(config_path: str, out_dir: str) -> None:
    """Run an injection-recovery grid from a YAML experiment config and
    write raw trial results, completeness-by-bin tables, and a false-
    positive-rate summary to ``out_dir``."""
    spec = yaml.safe_load(Path(config_path).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cadence = CadenceConfig(**spec.get("cadence", {}))
    channel = spec["channel"]
    grid = spec["grid"]
    fixed = spec.get("fixed", {})
    n_seeds = spec.get("n_seeds_per_point", 1)

    configs = []
    axes = list(grid.keys())
    import itertools

    for combo in itertools.product(*[grid[a] for a in axes]):
        params = dict(zip(axes, combo))
        for seed in range(n_seeds):
            configs.append(
                TrialConfig(channel=channel, cadence=cadence, seed=seed, **{**fixed, **params})
            )

    click.echo(f"Running {len(configs)} trials ...")
    df = run_grid(configs)
    df.to_csv(out / "trials.csv", index=False)

    bin_cols = [a for a in axes if a in df.columns]
    if bin_cols:
        comp = completeness_by_bin(df, bin_cols)
        comp.to_csv(out / "completeness.csv", index=False)
        click.echo(f"Wrote {out/'completeness.csv'} ({len(comp)} bins)")

    click.echo(f"Wrote {out/'trials.csv'} ({len(df)} trials)")


@main.command("null-fpr")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", default="results", show_default=True)
@click.option("--n-trials", default=200, show_default=True)
def null_fpr_cmd(config_path: str, out_dir: str, n_trials: int) -> None:
    """Estimate the false-positive rate from pure-noise (no injected
    planet/FFP signal) realizations of the same cadence and noise model."""
    spec = yaml.safe_load(Path(config_path).read_text())
    cadence = CadenceConfig(**spec.get("cadence", {}))
    fixed = spec.get("fixed", {})
    fixed = {k: v for k, v in fixed.items() if k not in ("u0", "q")}

    configs = [
        TrialConfig(channel="ffp", u0=50.0, tE=fixed.get("tE", 20.0), q=0.0,
                    cadence=cadence, seed=seed, **{k: v for k, v in fixed.items() if k != "tE"})
        for seed in range(n_trials)
    ]
    df = run_grid(configs)
    result = false_positive_rate(df)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "false_positive_rate.json").write_text(json.dumps(result, indent=2))
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
