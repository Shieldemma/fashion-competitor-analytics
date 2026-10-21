"""Clean, enrich and classify.

Clean   - parse timestamps to UTC, deduplicate, enforce dtypes
Enrich  - Lagos-local time parts, audit-window flag, brand registry fields,
          derived engagement fields (NULL when any input is unknown)
Classify- audience-comment purchase intent + sentiment; caption seller signals
"""

from __future__ import annotations

import pandas as pd

from . import clean, intent, sentiment

POST_COLUMNS = [
    "post_id", "platform", "brand_handle", "display_name", "brand_in_registry", "owner_username", "is_collab",
    "is_pinned", "post_url", "shortcode", "post_type", "caption", "published_at_utc", "published_date_wat",
    "published_hour_wat", "published_weekday_wat", "in_audit_window", "likes", "likes_hidden", "comments_count",
    "interactions", "video_views", "video_plays", "follower_count_reference", "likes_per_1k_followers",
    "caption_shows_price", "caption_call_to_action", "caption_launch_or_restock", "comments_disabled",
    "data_source", "source_file", "source_sha256", "source_row", "file_modified_at_utc", "extracted_at_utc",
]
COMMENT_COLUMNS = [
    "comment_id", "post_id", "brand_handle", "parent_comment_id", "is_reply", "commenter_id", "is_account_reply",
    "is_audience", "text", "published_at_utc", "published_date_wat", "published_hour_wat", "published_weekday_wat",
    "post_in_audit_window", "post_is_collab", "comment_likes", "intent_label", "intent_signals",
    "intent_signal_count", "intent_reason", "intent_negated", "affordability_barrier", "post_purchase_feedback",
    "sentiment_polarity", "sentiment_label", "data_source", "source_file", "source_sha256", "source_row",
    "extracted_at_utc",
]
NULLABLE_INT = ["likes", "comments_count", "interactions", "video_views", "video_plays", "follower_count_reference",
                "published_hour_wat", "source_row"]


def _most_complete_first(df: pd.DataFrame, key: str) -> pd.DataFrame:
    order = df.notna().sum(axis=1).sort_values(ascending=False).index
    return df.loc[order].drop_duplicates(subset=[key], keep="first").sort_index()


def audit_window(published: pd.Series, days: int, end: str | None) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Window of `days` ending at `end` (inclusive), or at the newest post."""
    end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1) if end else published.max()
    if pd.isna(end_ts):
        raise ValueError("Cannot determine audit window: no valid post timestamps")
    return end_ts - pd.Timedelta(days=days), end_ts


def transform_posts(posts: pd.DataFrame, brand_cfg: dict, window_days: int, window_end: str | None) -> tuple[pd.DataFrame, dict]:
    df = _most_complete_first(posts, "post_id")
    df["published_at_utc"] = clean.parse_timestamp(df["published_at_raw"])
    df = clean.add_local_time_parts(df)

    registry = {b["brand_handle"]: b for b in brand_cfg["brands"]}
    df["brand_in_registry"] = df["brand_handle"].isin(registry)
    df["display_name"] = df["brand_handle"].map(lambda h: registry.get(h, {}).get("display_name", h))
    df["follower_count_reference"] = df["brand_handle"].map(lambda h: registry.get(h, {}).get("follower_count"))

    in_scope = df.loc[df["brand_in_registry"], "published_at_utc"]
    start, end = audit_window(in_scope if len(in_scope) else df["published_at_utc"], window_days, window_end)
    df["in_audit_window"] = df["published_at_utc"].between(start, end).fillna(False)

    likes = pd.to_numeric(df["likes"], errors="coerce")
    comments = pd.to_numeric(df["comments_count"], errors="coerce")
    followers = pd.to_numeric(df["follower_count_reference"], errors="coerce")
    df["interactions"] = (likes + comments).where(likes.notna() & comments.notna())
    df["likes_per_1k_followers"] = (likes / followers * 1000).where(followers > 0).round(3)

    signals = df["caption"].map(intent.caption_signals).apply(pd.Series)
    df["caption_shows_price"] = signals["shows_price"]
    df["caption_call_to_action"] = signals["call_to_action"]
    df["caption_launch_or_restock"] = signals["launch_or_restock"]

    for col in NULLABLE_INT:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ["is_collab", "is_pinned", "likes_hidden", "brand_in_registry", "in_audit_window"]:
        df[col] = df[col].fillna(False).astype(bool)
    window = {"start_utc": start.isoformat(), "end_utc": end.isoformat(), "days": window_days}
    return df[POST_COLUMNS].reset_index(drop=True), window


def transform_comments(comments: pd.DataFrame, posts: pd.DataFrame) -> pd.DataFrame:
    if comments.empty:
        return pd.DataFrame(columns=COMMENT_COLUMNS)
    df = _most_complete_first(comments, "comment_id")
    df["published_at_utc"] = clean.parse_timestamp(df["published_at_raw"])
    df = clean.add_local_time_parts(df)
    lookup = posts.set_index("post_id")
    df["post_in_audit_window"] = df["post_id"].map(lookup["in_audit_window"]).fillna(False).astype(bool)
    df["post_is_collab"] = df["post_id"].map(lookup["is_collab"]).fillna(False).astype(bool)
    df["is_account_reply"] = df["is_account_reply"].fillna(False).astype(bool)
    df["is_audience"] = ~df["is_account_reply"]

    results = df["text"].map(intent.classify)
    df["intent_label"] = results.map(lambda r: r.label)
    df["intent_signals"] = results.map(lambda r: "|".join(r.signals))
    df["intent_signal_count"] = results.map(lambda r: r.signal_count).astype("Int64")
    df["intent_reason"] = results.map(lambda r: r.reason)
    df["intent_negated"] = results.map(lambda r: r.negated)
    df["affordability_barrier"] = results.map(lambda r: "affordability_barrier" in r.signals)
    df["post_purchase_feedback"] = results.map(lambda r: "post_purchase_feedback" in r.signals)
    df["sentiment_polarity"] = df["text"].map(sentiment.polarity)
    df["sentiment_label"] = df["sentiment_polarity"].map(sentiment.label)
    df["comment_likes"] = pd.to_numeric(df["comment_likes"], errors="coerce").astype("Int64")
    df["source_row"] = pd.to_numeric(df["source_row"], errors="coerce").astype("Int64")
    return df[COMMENT_COLUMNS].reset_index(drop=True)
