"""Offline tests use small excerpts of the public 2018 WFIRST Microlensing
Data Challenge answer key (Penny et al.; github.com/microlensing-data-challenge/
data-challenge-1) embedded directly as fixtures, so the parser is verified
without a network dependency. A separate, explicitly marked network test
exercises the real download path.
"""
import json
from pathlib import Path

import pytest

from romanmlr.data import MDCPaths, load_event_info, load_master_truth

# Four real rows (one of each simulated event class) copied verbatim from
# Answers/master_file.txt, plus the file's real header/comment line.
_MASTER_EXCERPT = """# idx        Sky position                 |       Ds                                     |       DL    ML                                                   | u0        alpha       t0         tE        rE       thetaE    piE     rhos                      |   MP        a  inc    phase    q          s       period |                   |         F087s            W149s          |         F087l                 W149l     |   fs0    fs1      |     |   chi2 chi2
344 0 82 1.16162 -2.1181 269.165 -29.0207 | 3966 10.384 0.822 -13.6637 0.00876737 10 5 6 | 14434 9.197 0.2 -4.81764 4.30585 10 5 7.3 10.322 3651 5.07 0.212 | 0.234453 83.4397 1767.01716721 0.0864145 0.021388 0.00232554 5.34462 0.158284 9.83452 428.766 0 | 5.34149e-05 1 24.9118 147.77 0.000267075 45.5602 2.23577 | 1 561.144 560.852 | 21.3529 21.9598 21.1398 21.3249 21.3108 | 25.1052 26.2148 24.7657 25.0428 24.9704 | 0.228701 0.337147 | 1 0 | 0 1 0 4.29165e+09 dccv 344 dccv_0_82_344 1
18 0 52 0.489318 -3.30021 269.959 -30.1918 | 3356 10.572 0.999 -7.13878 2.37847 10 5 5.4 | 1867 7.975 0.678 -3.34128 4.17862 10 5 6.5 6.953 4385 4.68 0.614 | 2.16671 144.086 1414.31840479 36.8514 3.3655 0.422006 0.0729903 0.00104122 4.20256 158.879 0 | 0.031757 1.0961 -28.9142 359.054 0.0468392 0.325677 1.36214 | 3 522.608 1560.41 | 20.3979 20.7042 20.3513 20.4206 20.4397 | 21.4413 22.0982 21.2247 21.4254 21.4312 | 0.413613 0.557115 | 1 0 | 0 88076.6 0 348.477 | 2.05916318357533 ombin   0.462222 ombin_0_52_18 2
2683 4 87 1.21885 -0.937016 268.036 -28.3744 | 3589 9.675 0.886 -11.0197 2.98334 10 5 5.6 | 6183 6.105 0.25 6.54734 -4.97902 10 5 7.2 9.821 3311 5.01 0.254 | -1.52343 38.6665 1790.31690896 6.6877 2.15354 0.35275 0.171343 0.00120717 19.2873 558.186 0 | 0.00273006 49.2163 83.7988 270.63 0.0109202 2.48124 686.808 | 3 1195.56 3582.63 | 21.7205 22.7684 21.2468 21.5747 21.4953 | 24.3303 25.8764 23.8164 24.1969 24.1324 | 0.607462 0.744427 | 1 0 | 0 76240 0 6860.52 | 0.422001236489339 omcassan   0.613786 omcassan_4_87_2683 4
1694 0 82 1.17028 -2.26944 269.319 -29.0889 | 9926 7.939 0.212 -5.21511 2.25429 10 5 7.3 | 7615 7.133 0.25 3.50389 2.55332 10 5 7.2 9.821 4438 5.01 0.254 | -0.0712711 109.98 1582.21264422 1.85542 0.315663 0.0442539 0.321621 0.00280589 8.72413 294.996 0 | 0.0168913 1 -71.8999 203.842 0.0675651 2.92477 1.93568 | 1 358.244 357.732 | 24.8482 25.9076 24.4302 24.7332 24.6206 | 23.9757 25.0437 23.5763 23.8731 23.7614 | 0.0206938 0.0242225 | 1 0 | 0 117 0 36836.2 999999 999999 999999 999999 999999 999999 999999 999999 999999 8905.98 76994.9 7414.03 3.44036e+09 -2.69363e+11 2.10898e+13 93.1194 dcnormffp 0.842367 dcnormffp_0_82_1694 5
"""

_EVENT_INFO_EXCERPT = """ulwdc1_001 1 269.165 -29.0207 8.18 0.73 0.01 1.41 0.01
ulwdc1_002 2 269.959 -30.1918 8.09 0.49 0.01 0.95 0.01
"""


def test_master_truth_parses_all_four_event_classes():
    rows = [
        line for line in _MASTER_EXCERPT.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert len(rows) == 4

    # exercise the same parsing routine used by load_master_truth by writing
    # the excerpt to a throwaway cache and monkeypatching the fetch target.
    import romanmlr.data as data_mod

    def fake_fetch(url, cache_path, manifest_path):
        return _MASTER_EXCERPT.encode("utf-8")

    orig = data_mod._fetch
    data_mod._fetch = fake_fetch
    try:
        df = load_master_truth(MDCPaths(cache_dir=Path("unused")))
    finally:
        data_mod._fetch = orig

    assert len(df) == 4
    assert set(df["event_type"]) == {"dccv", "ombin", "omcassan", "dcnormffp"}
    row = df[df["idx"] == 344].iloc[0]
    assert row["u0"] == pytest.approx(0.234453)
    assert row["tE"] == pytest.approx(0.0864145)
    assert row["rhos"] == pytest.approx(0.158284)


def test_event_info_columns_and_types():
    import romanmlr.data as data_mod

    def fake_fetch(url, cache_path, manifest_path):
        return _EVENT_INFO_EXCERPT.encode("utf-8")

    orig = data_mod._fetch
    data_mod._fetch = fake_fetch
    try:
        df = load_event_info(MDCPaths(cache_dir=Path("unused")))
    finally:
        data_mod._fetch = orig

    assert list(df.columns) == [
        "event_name", "event_number", "ra_deg", "dec_deg", "distance_kpc",
        "A_W149", "sigma_A_W149", "A_Z087", "sigma_A_Z087",
    ]
    assert df.loc[0, "event_name"] == "ulwdc1_001"
    assert df.loc[0, "ra_deg"] == pytest.approx(269.165)


@pytest.mark.network
def test_real_download_and_manifest(tmp_path):
    from romanmlr.data import load_master_truth

    paths = MDCPaths(cache_dir=tmp_path)
    df = load_master_truth(paths)
    assert len(df) == 293
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert "master_file.txt" in manifest
    assert manifest["master_file.txt"]["sha256"]
