"""Command-line workflow for the synthetic point-lens recovery study."""
from __future__ import annotations

import importlib.metadata
import itertools
import json
import hashlib
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import click
import numpy as np
import pandas as pd
import yaml

from .cadence import CadenceConfig, generate_observation_times
from .completeness import completeness_by_bin, false_positive_rate
from .data import MDCPaths, load_event_info, load_master_truth
from .detect import blind_search_pspl, event_delta_chi2
from .injection_recovery import TrialConfig, run_grid
from .noise import NoiseConfig, add_noise


def _cadence(spec: dict) -> CadenceConfig:
    values = dict(spec.get("cadence", {}))
    if "season_start_days" in values:
        values["season_start_days"] = tuple(values["season_start_days"])
    return CadenceConfig(**values)


def _noise(spec: dict) -> NoiseConfig:
    return NoiseConfig(**spec.get("noise", {}))


def _manifest(spec: dict) -> dict:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--"], check=False,
        ).returncode != 0
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
        dirty = None
    packages = {}
    for name in ("numpy", "scipy", "pandas", "pyyaml", "click"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    return {
        "experiment_id": spec.get("experiment_id", "unspecified"),
        "scope": spec.get("scope", "unspecified"),
        "git_commit": commit,
        "git_dirty": dirty,
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": packages,
        "rng": "numpy.random.Generator(PCG64), one seed per trial",
    }


def _record_run_inputs(spec: dict, config_path: str, out: Path) -> None:
    shutil.copy2(config_path, out / "config.yaml")
    manifest = _manifest(spec)
    manifest["config_sha256"] = hashlib.sha256(Path(config_path).read_bytes()).hexdigest()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


@click.group()
def main() -> None:
    """romanmlr: scoped synthetic point-lens injection/recovery study."""


@main.command("fetch-data")
@click.option("--cache-dir", default="data/cache", show_default=True)
def fetch_data(cache_dir: str) -> None:
    """Cache public 2018 WFIRST Microlensing Data Challenge tables."""
    paths = MDCPaths(cache_dir=Path(cache_dir))
    info = load_event_info(paths)
    truth = load_master_truth(paths)
    click.echo(f"event_info: {len(info)} rows -> {paths.cache_dir/'event_info.txt'}")
    click.echo(f"master_truth: {len(truth)} rows -> {paths.cache_dir/'master_file.txt'}")


@main.command("run-grid")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", default="results", show_default=True)
def run_grid_cmd(config_path: str, out_dir: str) -> None:
    """Run a declared synthetic grid and retain raw and binned outputs."""
    spec = yaml.safe_load(Path(config_path).read_text())
    if spec.get("status", "").startswith("disabled") or spec.get("channel") == "planetary":
        raise click.ClickException("planetary runs are disabled pending independent validation")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cadence = _cadence(spec)
    noise = _noise(spec)
    grid = spec["grid"]
    axes = list(grid)
    configs = []
    for combo in itertools.product(*[grid[a] for a in axes]):
        params = dict(zip(axes, combo))
        for seed in range(int(spec.get("n_seeds_per_point", 1))):
            configs.append(
                TrialConfig(
                    channel=spec["channel"], cadence=cadence, noise=noise, seed=seed,
                    **{**spec.get("fixed", {}), **params},
                )
            )
    click.echo(f"Running {len(configs)} trials ...")
    df = run_grid(configs)
    df.to_csv(out / "trials.csv", index=False)
    bin_cols = [a for a in axes if a in df.columns]
    if bin_cols:
        completeness_by_bin(df, bin_cols).to_csv(out / "conditional_recovery.csv", index=False)
    _record_run_inputs(spec, config_path, out)
    click.echo(f"Wrote {out/'trials.csv'} ({len(df)} trials)")


@main.command("null-fpr")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", default="results", show_default=True)
@click.option("--n-trials", default=200, show_default=True, type=click.IntRange(min=1))
def null_fpr_cmd(config_path: str, out_dir: str, n_trials: int) -> None:
    """Run the identical blind search on simple synthetic constant-flux nulls."""
    spec = yaml.safe_load(Path(config_path).read_text())
    cadence = _cadence(spec)
    base_noise = _noise(spec)
    threshold = float(spec.get("fixed", {}).get("detection_threshold", 500.0))
    mag_ref = float(spec.get("fixed", {}).get("mag_ref", 21.0))
    rows = []
    for seed in range(n_trials):
        t = generate_observation_times(CadenceConfig(**{**asdict(cadence), "seed": seed}))
        noise = NoiseConfig(**{**asdict(base_noise), "seed": seed})
        mag, sigma_mag = add_noise(np.full(t.size, mag_ref), noise)
        flux = 10 ** (-0.4 * (mag - mag_ref))
        sigma_flux = np.maximum(np.abs(flux * np.log(10) * 0.4 * sigma_mag), 1e-6)
        fit = blind_search_pspl(t, flux, sigma_flux)
        statistic = event_delta_chi2(fit, flux, sigma_flux)
        rows.append({"seed": seed, "event_delta_chi2": statistic,
                     "event_detected": statistic > threshold})
    df = pd.DataFrame(rows)
    summary = false_positive_rate(df)
    summary["scope"] = "simple synthetic null under declared cadence/noise proxy"
    summary["threshold"] = threshold
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "null_trials.csv", index=False)
    (out / "null_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    _record_run_inputs(spec, config_path, out)
    click.echo(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
