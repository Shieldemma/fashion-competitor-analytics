"""Validate: data-quality checks with an auditable report.

Rows that cannot be used (no ID, no brand, orphan comments) are moved to a
quarantine table instead of being dropped silently. Everything else is kept
and the issue is counted in the validation report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .config import log

POST_REQUIRED = ["post_id", "platform", "brand_handle", "post_url", "published_at_raw", "caption",
                 "likes", "comments_count", "data_source", "source_file", "source_sha256"]
COMMENT_REQUIRED = ["comment_id", "post_id", "brand_handle", "text", "published_at_raw", "is_account_reply"]
KNOWN_PLATFORMS = {"instagram", "tiktok", "facebook", "x", "youtube"}


class SchemaError(ValueError):
    pass


@dataclass
class ValidationReport:
    issues: list[dict] = field(default_factory=list)

    def add(self, table: str, check: str, severity: str, count: int, detail: str = "", examples=None):
        if count:
            self.issues.append({
                "table": table, "check": check, "severity": severity, "count": int(count),
                "detail": detail, "examples": ", ".join(map(str, list(examples or [])[:3])),
            })

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.issues, columns=["table", "check", "severity", "count", "detail", "examples"])


def require_columns(df: pd.DataFrame, required: list[str], table: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SchemaError(f"{table}: missing required columns {missing}")


def validate_posts(posts: pd.DataFrame, registry: set[str], report: ValidationReport) -> tuple[pd.DataFrame, pd.DataFrame]:
    require_columns(posts, POST_REQUIRED, "posts")
    bad = posts["post_id"].isna() | posts["brand_handle"].isna() | posts["post_url"].isna()
    quarantine = posts[bad].assign(quarantine_reason="missing post_id, brand or url")
    report.add("posts", "missing_identifier", "error", bad.sum(), "row quarantined", quarantine.get("source_row", []))
    posts = posts[~bad].copy()

    report.add("posts", "unknown_platform", "warning", (~posts["platform"].isin(KNOWN_PLATFORMS)).sum(),
               "platform not recognised", posts.loc[~posts["platform"].isin(KNOWN_PLATFORMS), "platform"].unique())
    not_registered = ~posts["brand_handle"].isin(registry)
    report.add("posts", "brand_not_in_registry", "warning", not_registered.sum(),
               "kept but excluded from competitor metrics", posts.loc[not_registered, "brand_handle"].unique())
    report.add("posts", "missing_timestamp", "warning", posts["published_at_raw"].isna().sum(), "cannot be placed in audit window")
    report.add("posts", "empty_caption", "info", (posts["caption"].fillna("") == "").sum())
    report.add("posts", "likes_hidden_by_platform", "info", posts.get("likes_hidden", pd.Series(dtype=bool)).fillna(False).sum(),
               "stored as NULL, not 0")
    report.add("posts", "likes_missing", "info", (posts["likes"].isna() & ~posts.get("likes_hidden", False)).sum(), "stored as NULL")
    report.add("posts", "collab_post", "info", posts.get("is_collab", pd.Series(dtype=bool)).sum(),
               "owned by another account but shown on the competitor's grid")
    dupes = posts["post_id"].duplicated(keep=False)
    report.add("posts", "duplicate_post_id", "warning", posts["post_id"].duplicated().sum(), "deduplicated", posts.loc[dupes, "post_id"].unique())
    return posts, quarantine


def validate_comments(comments: pd.DataFrame, post_ids: set[str], report: ValidationReport) -> tuple[pd.DataFrame, pd.DataFrame]:
    if comments.empty:
        return comments, comments.assign(quarantine_reason=pd.Series(dtype=str))
    require_columns(comments, COMMENT_REQUIRED, "comments")
    orphan = ~comments["post_id"].isin(post_ids) | comments["comment_id"].isna()
    quarantine = comments[orphan].assign(quarantine_reason="no matching post or no id")
    report.add("comments", "orphan_or_missing_id", "error", orphan.sum(), "row quarantined")
    comments = comments[~orphan].copy()
    report.add("comments", "empty_text", "info", (comments["text"].fillna("") == "").sum())
    report.add("comments", "account_reply", "info", comments["is_account_reply"].sum(), "brand/collaborator replies excluded from audience metrics")
    report.add("comments", "duplicate_comment_id", "warning", comments["comment_id"].duplicated().sum(), "deduplicated")
    return comments, quarantine


def log_report(report: ValidationReport) -> None:
    for issue in report.issues:
        level = {"error": log.error, "warning": log.warning}.get(issue["severity"], log.info)
        level("Validate [%s] %s: %d %s", issue["table"], issue["check"], issue["count"], issue["detail"])
