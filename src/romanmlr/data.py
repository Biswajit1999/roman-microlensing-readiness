"""Adapter for the public 2018 WFIRST (now Roman) Microlensing Data Challenge.

Source: https://github.com/microlensing-data-challenge/data-challenge-1
(Matthew Penny et al.; see docs/DATA_SOURCES.md for full provenance,
licence notes, and access dates). 293 simulated light curves (single lenses,
binary-star lenses, planetary binary lenses, and cataclysmic-variable
contaminants) with cadence, baseline length, and photometric noise designed
to mimic the WFIRST/Roman Galactic Bulge Time Domain Survey.

This module never redistributes the raw dataset inside the repository (the
light-curve archive alone is >100 MB); it downloads on demand into a local,
git-ignored cache and records a checksum manifest of everything it fetches.
"""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

BASE_URL = "https://raw.githubusercontent.com/microlensing-data-challenge/data-challenge-1/master/"
LC_TARBALL_URL = BASE_URL + "lc.tar.gz"
EVENT_INFO_URL = BASE_URL + "event_info.txt"
MASTER_FILE_URL = BASE_URL + "Answers/master_file.txt"

EVENT_INFO_COLUMNS = [
    "event_name",
    "event_number",
    "ra_deg",
    "dec_deg",
    "distance_kpc",
    "A_W149",
    "sigma_A_W149",
    "A_Z087",
    "sigma_A_Z087",
]

# Subset of Answers/wfirstColumnNumbers.txt used by this project; see
# docs/DATA_SOURCES.md for the complete column dictionary and provenance.
MASTER_COLUMN_INDEX = {
    "u0": 30,
    "alpha_deg": 31,
    "t0": 32,
    "tE": 33,
    "rE_au": 34,
    "thetaE_mas": 35,
    "piE": 36,
    "rhos": 37,
    "Mp_msun": 42,
    "a_au": 43,
    "q": 46,
    "s": 47,
}


def _sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(url: str, cache_path: Path, manifest_path: Path) -> bytes:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        return cache_path.read_bytes()

    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()

    cache_path.write_bytes(data)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "url": url,
        "sha256": _sha256_of_bytes(data),
        "n_bytes": len(data),
        "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    manifest[cache_path.name] = entry
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return data


@dataclass(frozen=True)
class MDCPaths:
    cache_dir: Path

    @property
    def manifest(self) -> Path:
        return self.cache_dir / "manifest.json"


def load_event_info(paths: MDCPaths) -> pd.DataFrame:
    raw = _fetch(EVENT_INFO_URL, paths.cache_dir / "event_info.txt", paths.manifest)
    df = pd.read_csv(io.BytesIO(raw), sep=r"\s+", header=None, names=EVENT_INFO_COLUMNS)
    return df


def load_master_truth(paths: MDCPaths) -> pd.DataFrame:
    """Ground-truth injected parameters for every 2018 Data Challenge event.

    Parses only the whitespace-separated numeric columns needed by this
    project (see MASTER_COLUMN_INDEX); the raw file also embeds literal
    ``|`` separator tokens between logical column groups which are dropped
    here, and the final columns are free-text event-type / filename fields
    handled separately.
    """
    raw = _fetch(MASTER_FILE_URL, paths.cache_dir / "master_file.txt", paths.manifest)
    text = raw.decode("utf-8")
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        tokens = line.split()
        numeric_tokens = [tok for tok in tokens if tok != "|"]
        rows.append(numeric_tokens)

    # Build a stripped-column index map once, using the first row's token
    # count vs. its '|'-bearing counterpart to locate true column offsets.
    template_line = next(l for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#"))
    template_tokens = template_line.split()
    stripped_positions = []
    n_stripped = 0
    for tok in template_tokens:
        if tok == "|":
            n_stripped += 1
            stripped_positions.append(None)
        else:
            stripped_positions.append(len(stripped_positions) - n_stripped)
    col_to_stripped = {orig: stripped for orig, stripped in enumerate(stripped_positions) if stripped is not None}

    data = {"idx": []}
    for name in MASTER_COLUMN_INDEX:
        data[name] = []
    data["event_type"] = []
    data["lc_root"] = []

    for tokens in rows:
        numeric_tokens = [tok for tok in tokens if tok != "|"]
        data["idx"].append(int(numeric_tokens[0]))
        for name, orig_col in MASTER_COLUMN_INDEX.items():
            stripped_col = col_to_stripped.get(orig_col)
            try:
                data[name].append(float(numeric_tokens[stripped_col]))
            except (TypeError, ValueError, IndexError):
                data[name].append(np.nan)
        # event type / lc-root filename are free-text tokens near the end;
        # locate them by pattern rather than fixed offset since count of
        # trailing columns differs by event class (see Answers/additional_columns.txt).
        text_tokens = [t for t in numeric_tokens if not _is_float(t)]
        data["event_type"].append(text_tokens[0] if text_tokens else "unknown")
        lc_root = next((t for t in numeric_tokens if "_" in t and not _is_float(t)), None)
        data["lc_root"].append(lc_root)

    return pd.DataFrame(data)


def _is_float(tok: str) -> bool:
    try:
        float(tok)
        return True
    except ValueError:
        return False


def load_light_curve(event_lc_root: str, filt: str, paths: MDCPaths) -> pd.DataFrame:
    """Load one BJD/Magnitude/Error light curve from the cached lc.tar.gz.

    ``filt`` is "W149" or "Z087". Downloads and caches the full tarball on
    first use (~100 MB); subsequent calls read from the local cache only.
    """
    tar_path = paths.cache_dir / "lc.tar.gz"
    if not tar_path.exists():
        _fetch(LC_TARBALL_URL, tar_path, paths.manifest)

    member = f"lc/{event_lc_root}_{filt}.txt"
    with tarfile.open(tar_path, "r:gz") as tar:
        try:
            f = tar.extractfile(member)
        except KeyError:
            raise FileNotFoundError(f"{member} not found in lc.tar.gz")
        if f is None:
            raise FileNotFoundError(f"{member} not found in lc.tar.gz")
        raw = f.read()

    df = pd.read_csv(io.BytesIO(raw), sep=r"\s+", header=None, names=["bjd", "mag", "err"])
    return df
