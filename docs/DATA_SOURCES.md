# Data Sources

## 2018 WFIRST (now Roman) Microlensing Data Challenge

- **Provider**: Matthew Penny (Louisiana State University) and the WFIRST
  microlensing science team.
- **URL**: <https://github.com/microlensing-data-challenge/data-challenge-1>
- **Accessed**: 2026-08-28 (event_info.txt, Answers/master_file.txt,
  Answers/wfirstColumnNumbers.txt, Answers/additional_columns.txt, README.md
  fetched and inspected directly; `lc.tar.gz`, the ~100 MB light-curve
  archive, is fetched on demand by `romanmlr fetch-data` / `src/romanmlr/data.py`
  and is not committed to this repository).
- **Licence**: no explicit licence file is published in the source
  repository; the data are described there as public and intended for
  community use in developing and testing microlensing analysis pipelines.
  This project does not redistribute the archive; it downloads directly
  from the upstream GitHub repository at run time and records a SHA-256
  checksum manifest of everything it fetches
  (`data/cache/manifest.json`, git-ignored, regenerated locally).
- **Content**: 293 simulated light curves in two filters (W149, Z087),
  spanning four injected classes: `dcnormffp` (74, single lens / isolated
  point-lens events including free-floating-planet analogs), `ombin` (83,
  binary star lenses), `omcassan` (43, bound planetary binary lenses),
  `dccv` (93, cataclysmic-variable contaminants -- **not** microlensing
  events, included to test false-positive rejection). These counts were
  independently reproduced by this project's parser
  (`src/romanmlr/data.py::load_master_truth`) and match the published class
  counts (verified 2026-08-28; see `docs/VALIDATION.md`).
- **Ground truth**: `Answers/master_file.txt` provides injected parameters
  (u0, t0, tE, rho, piE, and, for binary events, planet mass, semi-major
  axis, mass ratio q, and projected separation s) for every event. This
  project's `MASTER_COLUMN_INDEX` maps a documented subset of these columns
  (see `Answers/wfirstColumnNumbers.txt` in the upstream repository); the
  full column dictionary is not reproduced here to avoid drift from the
  upstream file, which remains the authoritative reference.
- **Cadence realism**: per the upstream README, light curves "mimic the
  cadence, length, and noise properties of the multi-year WFIRST Bulge
  survey" as understood in 2018; they predate the final Roman GBTDS design
  and are used here as an external realism check, not as the primary
  synthetic-injection cadence (see docs/METHODS.md).

## Roman Microlensing Data Challenge 2026 (RMDC26)

- **Provider**: RGES Project Infrastructure Team (RGES-PIT).
- **URL**: <https://rges-pit.org/data-challenge/>; data hosted on the Roman
  Research Nexus (<https://roman.science.stsci.edu/>) and Hugging Face
  (`RGES-PIT/Experienced`, `RGES-PIT/Beginner`).
- **Status as of 2026-08-28**: an active community data challenge
  (experienced-tier submissions close 2026-10-02). This project does **not**
  submit to RMDC26 and makes no RMDC26 leaderboard claims; it is noted here
  as a live, more current alternative data source that a future contribution
  could adapt to (see `docs/LIMITATIONS.md` and the repository Issues).

## Roman GBTDS survey-design references (not data; used for cadence parameters)

- Penny, M. T., et al. (2019), "Predictions of the Nancy Grace Roman Space
  Telescope Galactic Exoplanet Survey I," ApJS, 241, 3.
- Johnson, S. A., et al. (2020), "Predictions of the Nancy Grace Roman Space
  Telescope Galactic Exoplanet Survey II: Free-floating Planet Detection
  Rates," AJ, 160, 123.
- STScI Roman User Documentation, "Galactic Bulge Time-Domain Survey":
  <https://roman-docs.stsci.edu/roman-community-defined-surveys/galactic-bulge-time-domain-survey>
  (community-defined survey description; the final as-flown design is set
  by the Roman project and may differ from the values used as defaults
  here -- see `src/romanmlr/cadence.py` docstring).

## Explicitly not used

No proprietary, embargoed, or authentication-gated dataset is used by this
repository's default pipeline. No real (non-simulated) Roman observations
exist yet as of the access date above.
