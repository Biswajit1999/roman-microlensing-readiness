"""Command-line workflow for the synthetic point-lens recovery study."""
from __future__ import annotations

import hashlib
import importlib.metadata
import itertools
import json
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
from .completeness import (
    completeness_by_bin,
    false_positive_rate,
    recovery_by_endpoint,
    wilson_interval,
)
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


def _stable_trial_seed(experiment_id: str, params: dict, replicate: int) -> int:
    """Return a stable, parameter-aware 32-bit seed for one grid trial."""
    payload = json.dumps(
        {"experiment_id": experiment_id, "params": params, "replicate": replicate},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _run_summary(df: pd.DataFrame) -> dict:
    summary = {"n_trials": len(df), "n_fit_failures": int((~df["fit_success"]).sum())}
    for endpoint in ("event_detected", "parameters_recovered"):
        k = int(df[endpoint].sum())
        point, low, high = wilson_interval(k, len(df))
        summary[endpoint] = {
            "n_success": k,
            "fraction": point,
            "ci_low": low,
            "ci_high": high,
        }
    return summary


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
    experiment_id = str(spec.get("experiment_id", "unspecified"))
    search_grid = tuple(spec.get("search_timescale_grid_days", (0.02, 0.08, 0.3, 1.0, 3.0)))
    for combo in itertools.product(*[grid[a] for a in axes]):
        params = dict(zip(axes, combo))
        for replicate in range(int(spec.get("n_seeds_per_point", 1))):
            seed = _stable_trial_seed(experiment_id, {**spec.get("fixed", {}), **params}, replicate)
            configs.append(
                TrialConfig(
                    channel=spec["channel"], cadence=cadence, noise=noise, seed=seed,
                    search_timescale_grid_days=search_grid,
                    **{**spec.get("fixed", {}), **params},
                )
            )
    click.echo(f"Running {len(configs)} trials ...")
    df = run_grid(configs)
    df.to_csv(out / "trials.csv", index=False)
    bin_cols = [a for a in axes if a in df.columns]
    if bin_cols:
        completeness_by_bin(df, bin_cols).to_csv(out / "conditional_recovery.csv", index=False)
        recovery_by_endpoint(df, bin_cols).to_csv(out / "recovery_by_endpoint.csv", index=False)
    (out / "run_summary.json").write_text(json.dumps(_run_summary(df), indent=2) + "\n")
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
    mag_ref = float(spec.get("null_mag_ref", spec.get("fixed", {}).get("mag_ref", 21.0)))
    search_grid = tuple(spec.get("search_timescale_grid_days", (0.02, 0.08, 0.3, 1.0, 3.0)))
    rows = []
    experiment_id = str(spec.get("experiment_id", "unspecified"))
    for replicate in range(n_trials):
        seed = _stable_trial_seed(experiment_id, {"null": True}, replicate)
        cadence_child, noise_child = np.random.SeedSequence(seed).spawn(2)
        cadence_seed = int(cadence_child.generate_state(1, dtype=np.uint32)[0])
        noise_seed = int(noise_child.generate_state(1, dtype=np.uint32)[0])
        t = generate_observation_times(CadenceConfig(**{**asdict(cadence), "seed": cadence_seed}))
        noise = NoiseConfig(**{**asdict(base_noise), "seed": noise_seed})
        mag, sigma_mag = add_noise(np.full(t.size, mag_ref), noise)
        flux = 10 ** (-0.4 * (mag - mag_ref))
        sigma_flux = np.maximum(np.abs(flux * np.log(10) * 0.4 * sigma_mag), 1e-6)
        fit = blind_search_pspl(t, flux, sigma_flux, timescale_grid_days=search_grid)
        statistic = event_delta_chi2(fit, flux, sigma_flux)
        rows.append({
            "replicate": replicate,
            "seed": seed,
            "cadence_seed": cadence_seed,
            "noise_seed": noise_seed,
            "event_delta_chi2": statistic,
            "event_detected": bool(fit.success and statistic > threshold),
            "fit_success": bool(fit.success),
        })
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
