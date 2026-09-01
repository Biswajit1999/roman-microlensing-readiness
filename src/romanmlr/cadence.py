"""Versioned synthetic proxy for the current Roman GBTDS high-cadence seasons.

The defaults encode six 70.5-day F146 season windows at 12.1-minute effective
sampling, with three early and three late windows across a five-year mission.
They are an explicit experiment configuration, not an operations timeline or
an official mission simulator. Multi-filter snapshots, the six-tile geometry,
low-cadence middle seasons, and unannounced operational losses are metadata or
out of scope rather than invented as periodic gaps.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CadenceConfig:
    survey_definition_id: str = "roman-gbtds-public-design-2026-08"
    season_start_days: tuple[float, ...] = (
        0.0, 182.625, 365.25, 1278.375, 1461.0, 1643.625,
    )
    season_length_days: float = 70.5
    cadence_minutes: float = 12.1
    primary_filter: str = "F146"
    n_tiles: int = 6
    random_dropout_frac: float = 0.0
    seed: int = 0

    def total_baseline_days(self) -> float:
        return max(self.season_start_days) + self.season_length_days if self.season_start_days else 0.0


def generate_observation_times(cfg: CadenceConfig) -> np.ndarray:
    """Generate observation epochs (days) for the configured GBTDS-like cadence.

    Deterministic given ``cfg.seed``. Returns a sorted 1-D array of times.
    """
    rng = np.random.default_rng(cfg.seed)
    cadence_days = cfg.cadence_minutes / (24.0 * 60.0)
    if cfg.season_length_days <= 0 or cfg.cadence_minutes <= 0:
        raise ValueError("season length and cadence must be positive")
    if not 0 <= cfg.random_dropout_frac < 1:
        raise ValueError("random_dropout_frac must satisfy 0 <= f < 1")

    all_times = []
    for season_start in cfg.season_start_days:
        t = float(season_start)
        season_end = season_start + cfg.season_length_days
        while t < season_end:
            all_times.append(t)
            t += cadence_days

    times = np.array(all_times)
    if cfg.random_dropout_frac > 0:
        keep = rng.random(times.size) >= cfg.random_dropout_frac
        times = times[keep]
    return np.sort(times)
