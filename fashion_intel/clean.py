"""Normalization helpers: pure functions with no I/O, so they are easy to test.

Guiding rule: when a value is unknown, return None/NaN, never 0. A hidden
like count is not the same as zero likes.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

from .config import LOCAL_TZ

# ── Numbers ─────────────────────────────────────────────────────────────────

_SUFFIX = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
_COUNT_RE = re.compile(r"^([0-9][0-9,]*(?:\.[0-9]+)?|\.[0-9]+)\s*([kmb]?)$")
_TRAILING_UNITS = re.compile(r"\s*(likes?|views?|plays?|comments?|followers?)\s*$")


def parse_count(value) -> int | None:
    """Parse an engagement count such as 1234, '1,234', '1.2K', '2.3M'.

    Returns None for missing, unparseable or negative values. Instagram
    reports hidden like counts as -1, so negatives mean 'not available'.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return int(round(value)) if value >= 0 else None
    text = str(value).strip().lower()
    text = _TRAILING_UNITS.sub("", text).strip()
    if text in {"", "nan", "none", "null", "n/a", "-"}:
        return None
    if text.startswith("-"):
        return None
    match = _COUNT_RE.match(text)
    if not match:
        return None
    number, suffix = match.groups()
    if suffix == "" and "," in number:
        # '1,234' thousands separators; reject malformed groupings like '1,2,3'
        if not re.fullmatch(r"[0-9]{1,3}(,[0-9]{3})+", number):
            return None
    number = float(number.replace(",", ""))
    return int(round(number * _SUFFIX[suffix]))


def parse_bool(value) -> bool | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "t"}:
        return True
    if text in {"false", "0", "no", "n", "f"}:
        return False
    return None


# ── Names, platforms, URLs ──────────────────────────────────────────────────

_PLATFORM_ALIASES = {
    "instagram": "instagram", "ig": "instagram", "insta": "instagram",
    "tiktok": "tiktok", "tik tok": "tiktok", "tik-tok": "tiktok",
    "facebook": "facebook", "fb": "facebook", "meta": "facebook",
    "x": "x", "twitter": "x", "twitter/x": "x",
    "youtube": "youtube", "yt": "youtube",
}
_PLATFORM_DOMAINS = {
    "instagram.com": "instagram", "tiktok.com": "tiktok", "facebook.com": "facebook",
    "fb.com": "facebook", "twitter.com": "x", "x.com": "x", "youtube.com": "youtube",
}


def normalize_platform(value=None, url: str | None = None) -> str | None:
    """Map free-text platform names (or a post URL) to a canonical name."""
    if value is not None and not (isinstance(value, float) and math.isnan(value)):
        key = str(value).strip().lower()
        if key in _PLATFORM_ALIASES:
            return _PLATFORM_ALIASES[key]
    if url:
        host = urlsplit(str(url).strip()).netloc.lower().removeprefix("www.").removeprefix("m.")
        for domain, name in _PLATFORM_DOMAINS.items():
            if host == domain or host.endswith("." + domain):
                return name
    return None


def normalize_handle(value) -> str | None:
    """'@Ziva Lagos ' -> None-safe lowercase handle; profile URLs -> handle."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if "/" in text:
        path = [p for p in urlsplit(text if "://" in text else "https://" + text).path.split("/") if p]
        text = path[0] if path else ""
    text = text.lstrip("@").strip().lower()
    return text or None


def normalize_url(value) -> str | None:
    """Canonical post URL: https, lowercase host, no query/fragment, trailing slash."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    if "://" not in text:
        text = "https://" + text
    parts = urlsplit(text)
    host = parts.netloc.lower()
    if host.startswith("m."):
        host = "www." + host[2:]
    path = parts.path if parts.path.endswith("/") else parts.path + "/"
    return urlunsplit(("https", host, path, "", ""))


_SHORTCODE_RE = re.compile(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")


def instagram_shortcode(url) -> str | None:
    if not url:
        return None
    match = _SHORTCODE_RE.search(str(url))
    return match.group(1) if match else None


# ── Text ────────────────────────────────────────────────────────────────────

def clean_text(value) -> str:
    """Unicode-normalise, unify quotes, collapse whitespace. Missing -> ''."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    if text.strip().lower() in {"nan", "none", "null"}:
        return ""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def pseudonymize(username, salt: str = "fashion-intel") -> str | None:
    """Stable one-way ID for a commenter, so we never publish private handles."""
    handle = normalize_handle(username)
    if not handle:
        return None
    return "user_" + hashlib.sha256(f"{salt}:{handle}".encode()).hexdigest()[:12]


# ── Time ────────────────────────────────────────────────────────────────────

def parse_timestamp(series: pd.Series) -> pd.Series:
    """Parse to timezone-aware UTC. Malformed values become NaT (not dropped).

    Naive timestamps (no offset) are assumed to be UTC, because that is what
    Apify and Instagram's `datetime` attribute emit.
    """
    parsed = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    return parsed


def add_local_time_parts(df: pd.DataFrame, ts_col: str = "published_at_utc", prefix: str = "") -> pd.DataFrame:
    """Add Lagos-local date, hour and weekday columns (WAT = UTC+1)."""
    local = df[ts_col].dt.tz_convert(LOCAL_TZ)
    df[f"{prefix}published_date_wat"] = local.dt.strftime("%Y-%m-%d").where(local.notna(), None)
    df[f"{prefix}published_hour_wat"] = local.dt.hour.astype("Int64")
    df[f"{prefix}published_weekday_wat"] = local.dt.day_name().where(local.notna(), None)
    return df


# ── Column names ────────────────────────────────────────────────────────────

COLUMN_ALIASES = {
    "brand": "brand_handle", "brand_handle": "brand_handle", "handle": "brand_handle", "account": "brand_handle",
    "platform": "platform", "network": "platform",
    "post_url": "post_url", "url": "post_url", "link": "post_url", "permalink": "post_url",
    "caption": "caption", "text": "caption", "description": "caption",
    "likes": "likes", "likescount": "likes", "like_count": "likes",
    "comments": "comments_count", "comments_count": "comments_count", "commentscount": "comments_count",
    "views": "video_views", "video_views": "video_views", "videoviewcount": "video_views",
    "followers": "follower_count_reported", "follower_count": "follower_count_reported",
    "post_date": "published_at_raw", "timestamp": "published_at_raw", "date": "published_at_raw",
    "created_at": "published_at_raw", "published_at": "published_at_raw",
    "post_type": "post_type", "type": "post_type",
}


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known column variants to canonical names (case/space-insensitive)."""
    renames = {}
    for col in df.columns:
        key = re.sub(r"[\s\-]+", "_", str(col).strip().lstrip("﻿")).lower()
        if key in COLUMN_ALIASES and COLUMN_ALIASES[key] not in renames.values():
            renames[col] = COLUMN_ALIASES[key]
    return df.rename(columns=renames)
