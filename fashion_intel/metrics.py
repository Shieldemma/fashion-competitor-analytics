"""Business metrics. Single source of truth for the report, the dashboard,
and the SQL-consistency tests. Every rate states its denominator.

Three different things, never interchangeable:
  1. a purchase-intent *signal*  - one comment classified "high"/"medium"
  2. a *person* expressing intent - a distinct (pseudonymised) commenter
  3. a *transaction*              - NOT observable in this data; no metric claims it
"""

from __future__ import annotations

import math

import pandas as pd

INTENT_ORDER = ["high", "medium", "low", "uncertain", "no_signal"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def safe_rate(numerator, denominator, scale: float = 100.0):
    """numerator/denominator*scale, or NaN when the denominator is 0/unknown."""
    try:
        if denominator is None or pd.isna(denominator) or denominator == 0:
            return float("nan")
        return float(numerator) / float(denominator) * scale
    except (TypeError, ValueError):
        return float("nan")


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion, in percent. (nan, nan) if n == 0."""
    if not n:
        return float("nan"), float("nan")
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return round(max(0.0, centre - half) * 100, 2), round(min(1.0, centre + half) * 100, 2)


# ── Scoping ─────────────────────────────────────────────────────────────────

def scope(posts: pd.DataFrame, comments: pd.DataFrame, *, window_only: bool = True, include_collab: bool = True,
          include_pinned: bool = True, registry_only: bool = True, brands=None, platforms=None,
          date_from=None, date_to=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter posts, then keep only audience comments on the remaining posts.

    date_from/date_to are Lagos-local calendar dates (inclusive), applied to the
    post's publication date.
    """
    p = posts
    if registry_only:
        p = p[p["brand_in_registry"]]
    if window_only:
        p = p[p["in_audit_window"]]
    if not include_collab:
        p = p[~p["is_collab"]]
    if not include_pinned:
        p = p[~p["is_pinned"]]
    if brands is not None:
        p = p[p["brand_handle"].isin(brands)]
    if platforms is not None:
        p = p[p["platform"].isin(platforms)]
    if date_from is not None:
        p = p[p["published_date_wat"] >= str(pd.Timestamp(date_from).date())]
    if date_to is not None:
        p = p[p["published_date_wat"] <= str(pd.Timestamp(date_to).date())]
    c = comments[comments["post_id"].isin(p["post_id"]) & comments["is_audience"]]
    return p, c


# ── Coverage ────────────────────────────────────────────────────────────────

def coverage_by_brand(posts: pd.DataFrame, comments: pd.DataFrame, brand_cfg: dict) -> pd.DataFrame:
    """Data coverage per registered competitor, including brands with no data."""
    rows = []
    for b in brand_cfg["brands"]:
        p = posts[posts["brand_handle"] == b["brand_handle"]]
        c = comments[comments["post_id"].isin(p["post_id"]) & comments["is_audience"]]
        reported = p["comments_count"].sum(min_count=1)
        rows.append({
            "brand_handle": b["brand_handle"],
            "display_name": b["display_name"],
            "posts_collected": len(p),
            "posts_in_window": int(p["in_audit_window"].sum()),
            "first_post_wat": p["published_date_wat"].min() if len(p) else None,
            "last_post_wat": p["published_date_wat"].max() if len(p) else None,
            "collab_posts": int(p["is_collab"].sum()),
            "pinned_posts": int(p["is_pinned"].sum()),
            "likes_hidden_posts": int(p["likes_hidden"].sum()),
            "sampled_audience_comments": len(c),
            "reported_comments_total": None if pd.isna(reported) else int(reported),
            "comment_sample_pct": round(safe_rate(len(c), reported), 2),
            "follower_count_reference": b.get("follower_count"),
            "status": "no data collected" if p.empty else ("thin: <10 posts in window" if p["in_audit_window"].sum() < 10 else "ok"),
        })
    return pd.DataFrame(rows)


# ── Engagement ──────────────────────────────────────────────────────────────

def engagement_summary(posts: pd.DataFrame, by: list[str] | str = "brand_handle") -> pd.DataFrame:
    """Per-post engagement. Medians are primary because a few viral posts dominate means.

    Denominator for each statistic = posts where that value is known
    (hidden likes are excluded, not counted as zero).
    """
    by = [by] if isinstance(by, str) else by
    if posts.empty:
        return pd.DataFrame(columns=by + ["posts"])
    g = posts.groupby(by, dropna=False)
    out = g.agg(
        posts=("post_id", "count"),
        posts_likes_known=("likes", "count"),
        median_likes=("likes", "median"),
        mean_likes=("likes", "mean"),
        median_comments=("comments_count", "median"),
        median_interactions=("interactions", "median"),
        median_likes_per_1k_followers=("likes_per_1k_followers", "median"),
        video_posts_with_views=("video_views", "count"),
        median_video_views=("video_views", "median"),
    ).reset_index()
    for col in ["median_likes", "mean_likes", "median_comments", "median_interactions", "median_video_views"]:
        out[col] = out[col].astype(float).round(1)
    out["median_likes_per_1k_followers"] = out["median_likes_per_1k_followers"].astype(float).round(2)
    return out


def caption_signal_summary(posts: pd.DataFrame, by: str = "brand_handle") -> pd.DataFrame:
    """Seller-side behaviour: % of posts whose caption shows a price / CTA / launch. Denominator = posts."""
    if posts.empty:
        return pd.DataFrame(columns=[by, "posts"])
    g = posts.groupby(by)
    out = g.agg(posts=("post_id", "count"), shows_price=("caption_shows_price", "sum"),
                call_to_action=("caption_call_to_action", "sum"), launch_or_restock=("caption_launch_or_restock", "sum")).reset_index()
    for col in ["shows_price", "call_to_action", "launch_or_restock"]:
        out[f"{col}_pct"] = [round(safe_rate(n, d), 1) for n, d in zip(out[col], out["posts"])]
    return out


# ── Purchase intent ─────────────────────────────────────────────────────────

def intent_summary(comments: pd.DataFrame, posts: pd.DataFrame, by: list[str] | str = "brand_handle") -> pd.DataFrame:
    """Audience purchase-intent signals.

    Denominator for *_rate_pct = sampled audience comments in the group
    (brand/collaborator replies excluded; emoji-only comments included).
    posts_with_high_pct uses posts that have >= 1 sampled comment.
    """
    by = [by] if isinstance(by, str) else by
    cols = by + ["sampled_comments", *INTENT_ORDER, "high_rate_pct", "high_or_medium", "high_or_medium_rate_pct",
                 "hm_ci_low", "hm_ci_high", "signals_per_100_comments", "high_intent_commenters",
                 "posts_with_sampled_comments", "posts_with_high", "posts_with_high_pct", "affordability_barrier",
                 "post_purchase_feedback"]
    if comments.empty:
        return pd.DataFrame(columns=cols)
    c = comments.merge(posts[["post_id", *[b for b in by if b not in comments.columns]]], on="post_id", how="left") \
        if any(b not in comments.columns for b in by) else comments
    rows = []
    for key, grp in c.groupby(by, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        n = len(grp)
        counts = grp["intent_label"].value_counts()
        high = int(counts.get("high", 0))
        hm = high + int(counts.get("medium", 0))
        lo, hi = wilson_interval(hm, n)
        posts_with = grp["post_id"].nunique()
        posts_high = grp.loc[grp["intent_label"] == "high", "post_id"].nunique()
        rows.append({
            **dict(zip(by, key)),
            "sampled_comments": n,
            **{lab: int(counts.get(lab, 0)) for lab in INTENT_ORDER},
            "high_rate_pct": round(safe_rate(high, n), 2),
            "high_or_medium": hm,
            "high_or_medium_rate_pct": round(safe_rate(hm, n), 2),
            "hm_ci_low": lo, "hm_ci_high": hi,
            "signals_per_100_comments": round(safe_rate(grp["intent_signal_count"].sum(), n), 2),
            "high_intent_commenters": grp.loc[grp["intent_label"] == "high", "commenter_id"].nunique(),
            "posts_with_sampled_comments": posts_with,
            "posts_with_high": posts_high,
            "posts_with_high_pct": round(safe_rate(posts_high, posts_with), 2),
            "affordability_barrier": int(grp["affordability_barrier"].sum()),
            "post_purchase_feedback": int(grp["post_purchase_feedback"].sum()),
        })
    return pd.DataFrame(rows, columns=cols)


# ── Volume and timing ───────────────────────────────────────────────────────

def posts_per_day(posts: pd.DataFrame) -> pd.DataFrame:
    if posts.empty:
        return pd.DataFrame(columns=["published_date_wat", "brand_handle", "posts"])
    return posts.groupby(["published_date_wat", "brand_handle"]).size().rename("posts").reset_index()


def posting_time_summary(posts: pd.DataFrame, by: str = "published_weekday_wat") -> pd.DataFrame:
    """Posting time vs performance, comparable across brands of very different size.

    relative_performance = post interactions / that brand's median interactions
    (1.0 = typical for the brand). Median of that per time bucket.
    """
    p = posts.dropna(subset=["interactions", by]).copy()
    if p.empty:
        return pd.DataFrame(columns=[by, "posts", "brands", "median_relative_performance"])
    brand_median = p.groupby("brand_handle")["interactions"].transform("median").astype(float)
    p["relative_performance"] = p["interactions"].astype(float) / brand_median.where(brand_median > 0)
    out = p.groupby(by).agg(posts=("post_id", "count"), brands=("brand_handle", "nunique"),
                            median_relative_performance=("relative_performance", "median")).reset_index()
    out["median_relative_performance"] = out["median_relative_performance"].round(2)
    if by == "published_weekday_wat":
        out[by] = pd.Categorical(out[by], WEEKDAYS, ordered=True)
        out = out.sort_values(by)
        out[by] = out[by].astype(str)
    else:
        out = out.sort_values(by)
    return out.reset_index(drop=True)


# ── Sensitivity ─────────────────────────────────────────────────────────────

SCENARIOS = {
    "audit_window (primary)": dict(window_only=True),
    "all_collected_posts": dict(window_only=False),
    "window_excl_collab": dict(window_only=True, include_collab=False),
    "window_excl_pinned": dict(window_only=True, include_pinned=False),
}


def sensitivity(posts: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
    """Does the brand ranking on high+medium intent rate survive reasonable data choices?"""
    frames = []
    for name, kwargs in SCENARIOS.items():
        p, c = scope(posts, comments, **kwargs)
        s = intent_summary(c, p)
        s["scenario"] = name
        frames.append(s)
    # extra scenario: denominator = comments that contain words (drop emoji-only)
    p, c = scope(posts, comments, window_only=True)
    text_only = c[~c["intent_reason"].isin(["empty", "mention_only", "no_text_emoji_or_symbols"])]
    s = intent_summary(text_only, p)
    s["scenario"] = "window_text_comments_only"
    frames.append(s)
    out = pd.concat(frames, ignore_index=True)
    out["rank_high_or_medium"] = out.groupby("scenario")["high_or_medium_rate_pct"].rank(ascending=False, method="min")
    return out[["scenario", "brand_handle", "sampled_comments", "high", "medium", "high_or_medium_rate_pct",
                "hm_ci_low", "hm_ci_high", "rank_high_or_medium"]]


# ── Headline KPIs (dashboard + report use this one function) ────────────────

def kpis(posts: pd.DataFrame, comments: pd.DataFrame) -> dict:
    """Headline numbers for an already-scoped (posts, audience comments) pair."""
    n = len(comments)
    labels = comments["intent_label"].value_counts() if n else pd.Series(dtype=int)
    high = int(labels.get("high", 0))
    hm = high + int(labels.get("medium", 0))
    lo, hi = wilson_interval(hm, n)
    return {
        "brands_with_posts": int(posts["brand_handle"].nunique()),
        "posts": len(posts),
        "sampled_comments": n,
        "high": high,
        "high_or_medium": hm,
        "high_rate_pct": round(safe_rate(high, n), 2),
        "high_or_medium_rate_pct": round(safe_rate(hm, n), 2),
        "hm_ci": (lo, hi),
        "high_intent_commenters": int(comments.loc[comments["intent_label"] == "high", "commenter_id"].nunique()) if n else 0,
        "median_interactions": float(posts["interactions"].median()) if posts["interactions"].notna().any() else float("nan"),
    }


# ── Executive views ─────────────────────────────────────────────────────────

NO_TEXT_REASONS = {"empty", "mention_only", "no_text_emoji_or_symbols"}
COMPOSITION_ORDER = ["High intent (explicit request)", "Medium (wants it)", "Uncertain",
                     "Compliment / product interest", "Emoji or tag only", "Other (no purchase cue)"]


def comment_category(comments: pd.DataFrame) -> pd.Series:
    """Plain-English bucket for each comment: what the audience actually wrote."""
    lab, reason = comments["intent_label"], comments["intent_reason"]
    out = pd.Series("Other (no purchase cue)", index=comments.index)
    out[lab == "high"] = COMPOSITION_ORDER[0]
    out[lab == "medium"] = COMPOSITION_ORDER[1]
    out[lab == "uncertain"] = COMPOSITION_ORDER[2]
    out[lab == "low"] = COMPOSITION_ORDER[3]
    out[(lab == "no_signal") & reason.isin(NO_TEXT_REASONS)] = COMPOSITION_ORDER[4]
    return out


def comment_composition(comments: pd.DataFrame, by: str = "brand_handle") -> pd.DataFrame:
    """Share of sampled audience comments in each category. Denominator = comments in the group."""
    if comments.empty:
        return pd.DataFrame(columns=[by, "category", "comments", "group_total", "share_pct"])
    df = comments.assign(category=comment_category(comments))
    out = df.groupby([by, "category"]).size().rename("comments").reset_index()
    out["group_total"] = out.groupby(by)["comments"].transform("sum")
    out["share_pct"] = (out["comments"] / out["group_total"] * 100).round(1)
    return out


def intent_funnel(comments: pd.DataFrame) -> pd.DataFrame:
    """From sampled comments down to purchases. The last step is not observable in public data."""
    n = len(comments)
    has_text = int((~comments["intent_reason"].isin(NO_TEXT_REASONS)).sum()) if n else 0
    any_cue = int(comments["intent_label"].isin(["high", "medium", "uncertain"]).sum()) if n else 0
    high = int((comments["intent_label"] == "high").sum()) if n else 0
    people = int(comments.loc[comments["intent_label"] == "high", "commenter_id"].nunique()) if n else 0
    steps = [("Audience comments sampled", n), ("Contain words (not just emoji/tags)", has_text),
             ("Mention shopping at all", any_cue), ("Explicit purchase request", high),
             ("Distinct people asking to buy", people), ("Verified purchases", None)]
    out = pd.DataFrame(steps, columns=["step", "count"])
    out["pct_of_sampled"] = [round(safe_rate(c, n), 2) if c is not None else float("nan") for c in out["count"]]
    out["order"] = range(len(out))
    return out
