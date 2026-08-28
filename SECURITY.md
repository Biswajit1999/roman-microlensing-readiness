# Security Policy

This is a research-analysis package with no network services, authentication,
or user-input execution paths beyond reading local files and fetching a
fixed, documented set of public astronomical-data URLs (see
`docs/DATA_SOURCES.md`).

## Reporting a vulnerability

If you find a security issue (e.g. an unsafe deserialization path, a
dependency with a known CVE, or unsafe handling of downloaded data), please
open a GitHub Issue labeled `security` or use GitHub's private vulnerability
reporting for this repository. Please do not include exploit details in a
public issue for anything more serious than a dependency version bump.

## Scope notes

- Network access is limited to `urllib.request` fetches of fixed HTTPS URLs
  under `github.com/microlensing-data-challenge` (see `src/romanmlr/data.py`).
- Downloaded files are cached and checksummed (`data/cache/manifest.json`)
  but not otherwise executed or evaluated.
