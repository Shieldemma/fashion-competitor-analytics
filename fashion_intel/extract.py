"""Extract: read a raw export into two tidy tables (posts, comments).

Raw files are opened read-only and never modified. Every output row carries
provenance: which file it came from, the file's SHA-256 hash, the row number,
and when the extraction ran.

Supported inputs
- Apify "Instagram Post Scraper" CSV export (the real data in this project)
- A generic posts CSV (brand, platform, post_url, caption, likes, ...), as
  produced by scraper/instagram_scraper.py or generate_sample_data.py
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import clean
from .config import log


@dataclass
class Extracted:
    posts: pd.DataFrame
    comments: pd.DataFrame
    source: dict
    issues: list[dict] = field(default_factory=list)


def file_fingerprint(path: Path) -> dict:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    stat = path.stat()
    return {
        "source_file": path.name,
        "source_sha256": sha.hexdigest(),
        "file_modified_at_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def detect_format(columns) -> str:
    cols = {str(c).strip().lstrip("﻿") for c in columns}
    if {"inputUrl", "shortCode", "ownerUsername"} <= cols:
        return "apify_instagram"
    if {"post_url"} <= cols and ({"brand"} <= cols or {"brand_handle"} <= cols):
        return "generic_posts"
    raise ValueError(
        "Unrecognised input format. Expected an Apify Instagram export "
        "(inputUrl, shortCode, ownerUsername ...) or a posts CSV with brand + post_url columns."
    )


def extract(path: Path, data_source: str | None = None) -> Extracted:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw input not found: {path}")
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=True)
    raw.columns = [str(c).strip().lstrip("﻿") for c in raw.columns]
    source = file_fingerprint(path)
    fmt = detect_format(raw.columns)
    source["input_format"] = fmt
    log.info("Extract: %s (%d rows, format=%s)", path.name, len(raw), fmt)
    if fmt == "apify_instagram":
        return _extract_apify(raw, source, data_source or "apify_instagram_post_scraper")
    return _extract_generic(raw, source, data_source or "generic_posts_csv")


# ── Apify ───────────────────────────────────────────────────────────────────

def _post_id(platform: str, shortcode: str | None, url: str | None) -> str | None:
    if shortcode:
        return f"{platform}:{shortcode}"
    if url:
        return f"{platform}:url:{hashlib.sha1(url.encode()).hexdigest()[:16]}"
    return None


def _extract_apify(raw: pd.DataFrame, source: dict, data_source: str) -> Extracted:
    issues: list[dict] = []
    posts, comments = [], []
    coauthor_cols = [c for c in raw.columns if re.fullmatch(r"coauthorProducers/\d+/username", c)]
    top_idx = sorted({int(m.group(1)) for c in raw.columns if (m := re.fullmatch(r"latestComments/(\d+)/text", c))})

    for row_no, row in raw.iterrows():
        brand = clean.normalize_handle(row.get("inputUrl"))
        if isinstance(row.get("error"), str) and row["error"].strip():
            issues.append({
                "stage": "extract", "severity": "warning", "check": "scraper_error_row",
                "detail": f"{brand}: {row['error']} - {row.get('errorDescription', '')}".strip(),
                "count": 1,
            })
            continue

        url = clean.normalize_url(row.get("url"))
        platform = clean.normalize_platform(url=url) or "instagram"
        shortcode = row.get("shortCode") if isinstance(row.get("shortCode"), str) else clean.instagram_shortcode(url)
        owner = clean.normalize_handle(row.get("ownerUsername"))
        coauthors = {clean.normalize_handle(row[c]) for c in coauthor_cols if isinstance(row[c], str)}
        raw_likes = row.get("likesCount")
        likes = clean.parse_count(raw_likes)
        post_id = _post_id(platform, shortcode, url)

        posts.append({
            "post_id": post_id,
            "platform": platform,
            "brand_handle": brand,
            "owner_username": owner,
            "is_collab": bool(owner and brand and owner != brand),
            "is_pinned": clean.parse_bool(row.get("isPinned")) or False,
            "post_url": url,
            "shortcode": shortcode,
            "post_type": (row.get("productType") if row.get("productType") == "clips" else row.get("type")) or None,
            "caption": clean.clean_text(row.get("caption")),
            "published_at_raw": row.get("timestamp"),
            "likes": likes,
            "likes_hidden": isinstance(raw_likes, str) and raw_likes.strip().startswith("-"),
            "comments_count": clean.parse_count(row.get("commentsCount")),
            "video_views": clean.parse_count(row.get("videoViewCount")),
            "video_plays": clean.parse_count(row.get("videoPlayCount")),
            "comments_disabled": clean.parse_bool(row.get("isCommentsDisabled")),
            "data_source": data_source,
            "source_row": int(row_no) + 2,  # +1 header, +1 for 1-based line numbers
            **source,
        })

        account_handles = {h for h in {brand, owner, *coauthors} if h}
        for i in top_idx:
            top = _apify_comment(row, f"latestComments/{i}", post_id, brand, account_handles, None, row_no, data_source, source)
            if top is None:
                continue
            comments.append(top)
            j = 0
            while f"latestComments/{i}/replies/{j}/text" in raw.columns:
                reply = _apify_comment(row, f"latestComments/{i}/replies/{j}", post_id, brand,
                                       account_handles, top["comment_id"], row_no, data_source, source)
                if reply is not None:
                    comments.append(reply)
                j += 1

    return Extracted(pd.DataFrame(posts), pd.DataFrame(comments), source, issues)


def _apify_comment(row, prefix, post_id, brand, account_handles, parent_id, row_no, data_source, source):
    text = row.get(f"{prefix}/text")
    cid = row.get(f"{prefix}/id")
    if not isinstance(text, str) and not isinstance(cid, str):
        return None
    username = row.get(f"{prefix}/ownerUsername")
    if not isinstance(username, str):
        username = row.get(f"{prefix}/owner/username")
    handle = clean.normalize_handle(username)
    comment_id = f"{post_id.split(':')[0]}:c:{cid}" if isinstance(cid, str) else \
        f"{post_id}:h:{hashlib.sha1(f'{handle}|{text}|{row.get(prefix + "/timestamp")}'.encode()).hexdigest()[:16]}"
    return {
        "comment_id": comment_id,
        "post_id": post_id,
        "brand_handle": brand,
        "parent_comment_id": parent_id,
        "is_reply": parent_id is not None,
        "commenter_id": clean.pseudonymize(handle),
        "is_account_reply": handle in account_handles if handle else False,
        "text": clean.clean_text(text),
        "published_at_raw": row.get(f"{prefix}/timestamp"),
        "comment_likes": clean.parse_count(row.get(f"{prefix}/likesCount")),
        "data_source": data_source,
        "source_row": int(row_no) + 2,
        **{k: source[k] for k in ("source_file", "source_sha256", "extracted_at_utc")},
    }


# ── Generic posts CSV ───────────────────────────────────────────────────────

def _extract_generic(raw: pd.DataFrame, source: dict, data_source: str) -> Extracted:
    df = clean.standardize_columns(raw.copy())
    posts = []
    for row_no, row in df.iterrows():
        url = clean.normalize_url(row.get("post_url"))
        platform = clean.normalize_platform(row.get("platform"), url) or "unknown"
        likes_raw = row.get("likes")
        likes = clean.parse_count(likes_raw)
        posts.append({
            "post_id": _post_id(platform, clean.instagram_shortcode(url) if platform == "instagram" else None, url),
            "platform": platform,
            "brand_handle": clean.normalize_handle(row.get("brand_handle")),
            "owner_username": clean.normalize_handle(row.get("brand_handle")),
            "is_collab": False,
            "is_pinned": False,
            "post_url": url,
            "shortcode": clean.instagram_shortcode(url),
            "post_type": row.get("post_type") if isinstance(row.get("post_type"), str) else None,
            "caption": clean.clean_text(row.get("caption")),
            "published_at_raw": row.get("published_at_raw"),
            "likes": likes,
            "likes_hidden": isinstance(likes_raw, str) and likes_raw.strip().startswith("-"),
            "comments_count": clean.parse_count(row.get("comments_count")),
            "video_views": clean.parse_count(row.get("video_views")),
            "video_plays": None,
            "comments_disabled": None,
            # a generic file may declare its own provenance (e.g. synthetic_sample)
            "data_source": row.get("data_source") if isinstance(row.get("data_source"), str) else data_source,
            "source_row": int(row_no) + 2,
            **source,
        })
    empty_comments = pd.DataFrame(columns=[
        "comment_id", "post_id", "brand_handle", "parent_comment_id", "is_reply", "commenter_id",
        "is_account_reply", "text", "published_at_raw", "comment_likes", "data_source", "source_row",
        "source_file", "source_sha256", "extracted_at_utc"])
    return Extracted(pd.DataFrame(posts), empty_comments, source, [])
