import math

import pandas as pd
import pytest

from fashion_intel import clean


@pytest.mark.parametrize("raw, expected", [
    ("1.2K", 1200), ("1.2k", 1200), ("2.3M", 2_300_000), ("1B", 1_000_000_000), (".5k", 500),
    ("1,234", 1234), ("12,345,678", 12_345_678), (" 15 likes", 15), ("3.4K views", 3400),
    (7, 7), (7.0, 7), ("7.0", 7), ("0", 0),
    ("-1", None), (-1, None), ("-1.0", None),          # Instagram "hidden" sentinel
    ("", None), (None, None), (float("nan"), None), ("nan", None), ("N/A", None),
    ("abc", None), ("1,2,3", None), ("12k5", None), (True, None),
])
def test_parse_count(raw, expected):
    assert clean.parse_count(raw) == expected


def test_parse_count_never_turns_unknown_into_zero():
    assert clean.parse_count("garbage") is None
    assert clean.parse_count("") is None


@pytest.mark.parametrize("value, url, expected", [
    ("Instagram", None, "instagram"), ("IG", None, "instagram"), (" tik tok ", None, "tiktok"),
    ("Twitter", None, "x"), ("fb", None, "facebook"),
    (None, "https://www.instagram.com/p/abc/", "instagram"), (None, "https://vm.tiktok.com/xyz", "tiktok"),
    ("myspace", None, None), (float("nan"), None, None),
])
def test_normalize_platform(value, url, expected):
    assert clean.normalize_platform(value, url) == expected


@pytest.mark.parametrize("raw, expected", [
    ("@ZivaLagos ", "zivalagos"), ("https://www.instagram.com/ashluxe/ ", "ashluxe"),
    ("instagram.com/wflsncrm", "wflsncrm"), ("", None), (None, None), (float("nan"), None),
])
def test_normalize_handle(raw, expected):
    assert clean.normalize_handle(raw) == expected


def test_normalize_url_and_shortcode():
    url = clean.normalize_url(" http://WWW.Instagram.com/p/DXRmu0fjWce?igsh=abc#x ")
    assert url == "https://www.instagram.com/p/DXRmu0fjWce/"
    assert clean.instagram_shortcode(url) == "DXRmu0fjWce"
    assert clean.instagram_shortcode("https://www.instagram.com/reel/C_1-x/") == "C_1-x"
    assert clean.normalize_url("") is None and clean.normalize_url(None) is None


def test_clean_text():
    assert clean.clean_text(None) == ""
    assert clean.clean_text(float("nan")) == ""
    assert clean.clean_text("nan") == ""
    assert clean.clean_text("  It’s   gorgeous\n\n") == "It's gorgeous"


def test_pseudonymize_is_stable_and_hides_handle():
    a, b = clean.pseudonymize("@Fan_One"), clean.pseudonymize("fan_one")
    assert a == b and a.startswith("user_") and "fan_one" not in a
    assert clean.pseudonymize(None) is None


def test_parse_timestamp_malformed_becomes_nat():
    s = clean.parse_timestamp(pd.Series(["2026-04-18T13:42:42.000Z", "not-a-date", None, "2026-04-18 13:42:42"]))
    assert str(s.iloc[0].tz) == "UTC"
    assert s.isna().tolist() == [False, True, True, False]


def test_local_time_is_wat_not_utc():
    df = pd.DataFrame({"published_at_utc": clean.parse_timestamp(pd.Series(["2026-04-20T23:30:00Z", None]))})
    df = clean.add_local_time_parts(df)
    # 23:30 UTC on Monday 20 April is 00:30 WAT on Tuesday 21 April
    assert df.loc[0, "published_hour_wat"] == 0
    assert df.loc[0, "published_date_wat"] == "2026-04-21"
    assert df.loc[0, "published_weekday_wat"] == "Tuesday"
    assert pd.isna(df.loc[1, "published_hour_wat"])


def test_standardize_columns_handles_variants():
    df = pd.DataFrame(columns=["﻿Brand", "Post URL", "likesCount", "Timestamp", "Followers"])
    out = clean.standardize_columns(df)
    assert list(out.columns) == ["brand_handle", "post_url", "likes", "published_at_raw", "follower_count_reported"]
