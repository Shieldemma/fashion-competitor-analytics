"""Report: write reports/findings_generated.md from this run's metric tables.

This file contains only numbers computed by the pipeline plus fixed caveats.
Interpretation lives in reports/executive_summary.md, written by a human
against these numbers.
"""

from __future__ import annotations

import math

import pandas as pd

from .config import REPORTS_DIR


def md_table(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return "_No rows in scope._\n"
    d = df[cols] if cols else df
    d = d.head(max_rows)

    def fmt(v):
        if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA:
            return "–"
        if isinstance(v, float):
            return f"{v:,.2f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:,.0f}"
        if isinstance(v, (int,)) and not isinstance(v, bool):
            return f"{v:,}"
        return str(v)

    lines = ["| " + " | ".join(d.columns) + " |", "|" + "|".join("---" for _ in d.columns) + "|"]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join(lines) + "\n"


def write_findings(tables: dict[str, pd.DataFrame], manifest: dict, validation: pd.DataFrame) -> str:
    w = manifest["audit_window"]
    src = manifest["source"]
    platforms = tables["intent_by_platform"]["platform"].tolist() if not tables["intent_by_platform"].empty else []
    parts = [
        "# Generated Findings (auto-generated — do not edit by hand)\n",
        f"Run `{manifest['run_id']}` · code v{manifest['code_version']} · generated {manifest['finished_at_utc']}\n",
        "## Provenance\n",
        f"- Source file: `{src['source_file']}` (SHA-256 `{src['source_sha256'][:16]}…`), format `{src['input_format']}`",
        f"- Source file last modified: {src['file_modified_at_utc'][:19]} UTC (proxy for collection date; the export has no scrape timestamp)",
        f"- Audit window: {w['start_utc'][:10]} → {w['end_utc'][:10]} ({w['days']} days, UTC)",
        f"- Rows: {manifest['rows']['posts']} posts, {manifest['rows']['audience_comments']} audience comments "
        f"({manifest['rows']['comments']} incl. brand replies); quarantined: {manifest['rows']['quarantined_posts']} posts, "
        f"{manifest['rows']['quarantined_comments']} comments",
        f"- Platforms present: {', '.join(platforms) or 'none'}\n",
        "## Data coverage per competitor (all collected posts)\n",
        md_table(tables["coverage_by_brand"], ["display_name", "posts_collected", "posts_in_window", "first_post_wat",
                                               "last_post_wat", "collab_posts", "likes_hidden_posts",
                                               "sampled_audience_comments", "reported_comments_total",
                                               "comment_sample_pct", "status"]),
        "`comment_sample_pct` = sampled audience comments ÷ comment total reported by Instagram. "
        "The scraper returns only the ~10 latest comments per post.\n",
        "## Audience purchase-intent signals by brand (audit window)\n",
        "Denominator: sampled audience comments on in-window posts. "
        "`hm` = high + medium. CI = 95% Wilson interval for the high+medium rate.\n",
        md_table(tables["intent_by_brand"], ["brand_handle", "sampled_comments", "high", "medium", "low", "uncertain",
                                             "no_signal", "high_rate_pct", "high_or_medium_rate_pct", "hm_ci_low",
                                             "hm_ci_high", "high_intent_commenters", "posts_with_high",
                                             "posts_with_sampled_comments"]),
        "## By platform (audit window)\n",
        md_table(tables["intent_by_platform"], ["platform", "sampled_comments", "high", "medium",
                                                "high_or_medium_rate_pct", "hm_ci_low", "hm_ci_high"]),
        "_A platform comparison needs at least two platforms. Only the platforms listed above were collected._\n",
        "## Sensitivity: high+medium rate and rank under different data choices\n",
        md_table(tables["sensitivity"]),
        "## Engagement by brand (audit window; medians, hidden likes excluded)\n",
        md_table(tables["engagement_by_brand"], ["brand_handle", "posts", "posts_likes_known", "median_likes",
                                                 "median_comments", "median_interactions",
                                                 "median_likes_per_1k_followers", "median_video_views"]),
        "`median_likes_per_1k_followers` uses manually entered, unverified follower counts — reference only.\n",
        "## Seller-side caption behaviour (audit window; % of posts)\n",
        md_table(tables["caption_signals_by_brand"], ["brand_handle", "posts", "shows_price_pct", "call_to_action_pct",
                                                      "launch_or_restock_pct"]),
        "## Posting day (audit window, Lagos time)\n",
        "`median_relative_performance` = post interactions ÷ that brand's median (1.0 = typical).\n",
        md_table(tables["posting_weekday"]),
        "## Data-quality issues\n",
        md_table(validation[["table", "check", "severity", "count", "detail"]] if not validation.empty else validation),
        "## What these numbers cannot show\n",
        "- Sales, conversions or revenue: none were observed. A `high` comment is a purchase-intent *signal*.",
        "- Causality: differences between brands are observational and confounded by audience size, content and niche.",
        "- Budget allocation across platforms: requires data from more than one platform plus spend/conversion data.",
    ]
    text = "\n".join(parts) + "\n"
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "findings_generated.md").write_text(text, encoding="utf-8")
    return text
