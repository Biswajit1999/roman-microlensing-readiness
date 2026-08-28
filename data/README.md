# data/

No raw data is committed to this repository. Run `romanmlr fetch-data` to
download and cache the public 2018 WFIRST/Roman Microlensing Data Challenge
ground-truth tables into `data/cache/` (git-ignored); the light-curve
archive (`lc.tar.gz`) is fetched lazily on first use of
`romanmlr.data.load_light_curve`. See `docs/DATA_SOURCES.md` for full
provenance and `data/manifests/` for the checksum manifest schema.
