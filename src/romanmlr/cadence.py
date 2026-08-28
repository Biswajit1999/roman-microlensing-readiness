"""Roman Galactic Bulge Time Domain Survey (GBTDS) observing-cadence model.

Parameters default to the widely used community design reference, Penny et al.
(2019, ApJS 241, 3): six ~72-day bulge seasons per year near opposition,
continuous ~15-minute cadence in the wide W149 filter while a field is being
observed, with gaps between seasons (Earth/Sun avoidance) and a per-orbit
downlink/settling gap. The as-flown Roman GBTDS design is finalized by the
project (see https://roman-docs.stsci.edu/roman-community-defined-surveys/
galactic-bulge-time-domain-survey); this module treats every value below as a
configurable assumption, not an official specification, and every generated
window is stamped with the parameters used to produce it (see
docs/DATA_SOURCES.md).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CadenceConfig:
    n_seasons: int = 6
    season_length_days: float = 72.0
    season_gap_days: float = 61.0  # ~ half-year gap while bulge is unobservable
    cadence_minutes: float = 15.0
    downlink_gap_every_hours: float = 12.0  # simplified periodic data-gap proxy
    downlink_gap_minutes: float = 40.0
    random_dropout_frac: float = 0.02  # missed exposures (safing, cosmic rays, ...)
    t0_days: float = 0.0
    seed: int = 0

    def total_baseline_days(self) -> float:
        return self.n_seasons * self.season_length_days + (self.n_seasons - 1) * self.season_gap_days


def generate_observation_times(cfg: CadenceConfig) -> np.ndarray:
    """Generate observation epochs (days) for the configured GBTDS-like cadence.

    Deterministic given ``cfg.seed``. Returns a sorted 1-D array of times.
    """
    rng = np.random.default_rng(cfg.seed)
    cadence_days = cfg.cadence_minutes / (24.0 * 60.0)
    downlink_period_days = cfg.downlink_gap_every_hours / 24.0
    downlink_gap_days = cfg.downlink_gap_minutes / (24.0 * 60.0)

    all_times = []
    season_start = cfg.t0_days
    for _ in range(cfg.n_seasons):
        t = season_start
        season_end = season_start + cfg.season_length_days
        next_downlink = season_start + downlink_period_days
        while t < season_end:
            if t >= next_downlink:
                t += downlink_gap_days
                next_downlink += downlink_period_days
                continue
            all_times.append(t)
            t += cadence_days
        season_start = season_end + cfg.season_gap_days

    times = np.array(all_times)
    if cfg.random_dropout_frac > 0:
        keep = rng.random(times.size) >= cfg.random_dropout_frac
        times = times[keep]
    return np.sort(times)
