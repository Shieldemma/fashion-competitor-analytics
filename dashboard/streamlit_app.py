# dashboard/streamlit_app.py
# Run with:  streamlit run dashboard/streamlit_app.py
# Reads the pipeline outputs (data/processed/*.csv). Every number comes from
# fashion_intel.metrics, the same functions behind the report and SQL tests.

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))

import charts  # noqa: E402
from fashion_intel import metrics  # noqa: E402
from fashion_intel.config import PROCESSED_DIR, load_brand_config  # noqa: E402
from fashion_intel.pipeline import load_processed  # noqa: E402

st.set_page_config(page_title="Lagos Fashion Intelligence", page_icon="👗", layout="wide")

INTENT_NAMES = {"high": "High intent", "medium": "Medium intent", "low": "Low / product interest",
                "uncertain": "Uncertain", "no_signal": "No signal"}
GITHUB_URL = "https://github.com/Shieldemma"


# ── Data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    posts, comments, manifest = load_processed()
    return posts, comments, manifest, load_brand_config()


if not (PROCESSED_DIR / "posts.csv").exists():
    st.title("Lagos Fashion Competitor Intelligence")
    st.error("No pipeline outputs found. Run the pipeline first:")
    st.code("python -m fashion_intel run")
    st.stop()

try:
    posts_all, comments_all, manifest, brand_cfg = load()
except Exception as exc:  # readable message instead of a stack trace
    st.error(f"Could not read pipeline outputs: {exc}. Re-run `python -m fashion_intel run`.")
    st.stop()

registry = [b["brand_handle"] for b in brand_cfg["brands"]]
display = {b["brand_handle"]: b["display_name"] for b in brand_cfg["brands"]}
brand_scale = charts.brand_scale([display[h] for h in registry])
window = manifest.get("audit_window", {})
source = manifest.get("source", {})
is_synthetic = posts_all["data_source"].astype(str).str.contains("synthetic").any()
posts_all = posts_all.assign(brand=posts_all["brand_handle"].map(display).fillna(posts_all["brand_handle"]))
comments_all = comments_all.assign(brand=comments_all["brand_handle"].map(display).fillna(comments_all["brand_handle"]))

# ── Sidebar: filters + about ────────────────────────────────────────────────
st.sidebar.header("Filters")
brand_options = [h for h in registry if h in set(posts_all["brand_handle"])]
sel_brands = st.sidebar.multiselect("Brand", brand_options, default=brand_options, format_func=lambda h: display.get(h, h))
platform_options = sorted(posts_all["platform"].unique())
sel_platforms = st.sidebar.multiselect("Platform", platform_options, default=platform_options)
window_only = st.sidebar.toggle("Audit window only (60 days)", value=True,
                                help="Off = include every collected post, including older and pinned posts.")
dates = posts_all.loc[posts_all["in_audit_window"] if window_only else posts_all.index, "published_date_wat"].dropna()
dmin, dmax = pd.to_datetime(dates.min()).date(), pd.to_datetime(dates.max()).date()
date_range = st.sidebar.date_input("Post date (Lagos time)", value=(dmin, dmax), min_value=dmin, max_value=dmax)
sel_intents = st.sidebar.multiselect("Intent category (comment table)", list(INTENT_NAMES), default=list(INTENT_NAMES),
                                     format_func=INTENT_NAMES.get)
include_collab = st.sidebar.toggle("Include collab posts", value=True,
                                   help="Posts owned by a partner account but shown on the competitor's grid.")
include_pinned = st.sidebar.toggle("Include pinned posts", value=True)

with st.sidebar.expander("About this project", expanded=False):
    st.markdown(
        "End-to-end analytics case study based on a real Upwork brief.\n\n"
        "**Pipeline:** Apify scraping → validated Python ETL → rule-based NLP (Nigerian English & Pidgin) "
        "→ SQLite/PostgreSQL warehouse → this Streamlit dashboard.\n\n"
        "**Quality:** 125 automated tests, SQL and Python metrics cross-checked, data provenance on every row.\n\n"
        f"**Author:** Otuekong Emmanuel · [GitHub]({GITHUB_URL})"
    )

d_from, d_to = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (dmin, dmax)
scope_kwargs = dict(include_collab=include_collab, include_pinned=include_pinned, brands=sel_brands,
                    platforms=sel_platforms)
posts, comments = metrics.scope(posts_all, comments_all, window_only=window_only, date_from=d_from, date_to=d_to,
                                **scope_kwargs)

# ── Header ──────────────────────────────────────────────────────────────────
st.title("Lagos Fashion Competitor Intelligence")
st.markdown("**Which social platform shows the strongest purchase intent for Lagos fashion brands, and where should "
            "a retailer spend?** A two-month audit of public competitor data.")
if is_synthetic:
    st.error("**SYNTHETIC SAMPLE DATA.** These numbers are generated for demonstration and describe no real brand.")
else:
    st.caption(
        f"Data: public Instagram posts & comments via Apify (file `{source.get('source_file', '?')}`, "
        f"collected ≈{str(source.get('file_modified_at_utc', '?'))[:10]}) · audit window "
        f"{str(window.get('start_utc', '?'))[:10]} → {str(window.get('end_utc', '?'))[:10]} · "
        "purchase intent = rule-based classification of comment text (signals, not sales)")

if posts.empty:
    st.warning("No posts match these filters. Widen the date range or select more brands.")
    st.stop()

k = metrics.kpis(posts, comments)
hm_rate = "–" if pd.isna(k["high_or_medium_rate_pct"]) else f"{k['high_or_medium_rate_pct']:.1f}%"
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Competitors with data", f"{k['brands_with_posts']} of {len(registry)}", border=True)
c2.metric("Platforms collected", f"{posts['platform'].nunique()}", border=True,
          help="A platform comparison needs at least two.")
c3.metric("Posts in scope", f"{k['posts']:,}", border=True)
c4.metric("Audience comments analysed", f"{k['sampled_comments']:,}", border=True)
c5.metric("Shopping-signal rate", hm_rate, border=True,
          help=f"High + medium intent comments ÷ comments analysed. 95% CI {k['hm_ci'][0]}–{k['hm_ci'][1]}%.")

tabs = st.tabs(["📊 Executive summary", "🛒 Purchase intent", "❤️ Engagement", "🕒 Posting time",
                "🧭 Data coverage", "📘 Method", "🗂️ Data"])

# ── Executive summary ───────────────────────────────────────────────────────
with tabs[0]:
    # 1. The brief vs what the data can answer
    st.subheader("1 · The brief vs. what the data can answer")
    cov = metrics.coverage_by_brand(posts_all, comments_all, brand_cfg)
    n_brands = int((cov["posts_collected"] > 0).sum())
    n_platforms = posts_all["platform"].nunique()
    full_window = int((cov["posts_in_window"] >= 10).sum())
    s1, s2, s3, s4 = st.columns(4)
    with s1.container(border=True):
        st.markdown(f"**5 competitors**\n\n:orange[⚠ Partly met] — **{n_brands} of 5** returned data "
                    "(Yomi Casual: profile empty/private).")
    with s2.container(border=True):
        st.markdown("**Several platforms**\n\n" + (
            f":red[✕ Not met] — **{n_platforms} platform** collected (Instagram). Platforms can't be compared yet."
            if n_platforms < 2 else f":green[✓ Met] — {n_platforms} platforms collected."))
    with s3.container(border=True):
        st.markdown(f"**2-month window**\n\n:orange[⚠ Partly met] — **{full_window} of {n_brands}** brands have "
                    "≥10 posts in the window; others post rarely.")
    with s4.container(border=True):
        st.markdown(f"**Purchase-intent measure**\n\n:green[✓ Met] — **{len(comments_all[comments_all['is_audience']]):,}** "
                    "audience comments classified with a tested NLP rule set.")

    # 2. Funnel + what people write
    st.subheader("2 · How much purchase intent is in the comments?")
    left, right = st.columns([1, 1])
    with left.container(border=True):
        st.markdown("**From comments to purchases** (current filters)")
        st.altair_chart(charts.funnel(metrics.intent_funnel(comments)), width="stretch")
        st.caption("A comment is a *signal*; a person is a *buyer candidate*; a sale is never visible in public data.")
    with right.container(border=True):
        st.markdown("**What audiences actually write** (current filters)")
        comp = metrics.comment_composition(comments, "brand")
        if comp.empty:
            st.info("No comments in scope.")
        else:
            st.altair_chart(charts.composition(comp), width="stretch")
            share = comp.groupby("category")["comments"].sum() / comp["comments"].sum() * 100
            praise = share.get("Compliment / product interest", 0) + share.get("Emoji or tag only", 0)
            st.caption(f"**{praise:.0f}%** of comments are praise or emoji reactions.")

    # 3. Window vs all posts
    st.subheader("3 · Where the buying questions are: recent vs. older posts")
    rows = []
    for name, w_only in [("Audit window (60 days)", True), ("All collected posts", False)]:
        p_s, c_s = metrics.scope(posts_all, comments_all, window_only=w_only, **scope_kwargs)
        s = metrics.intent_summary(c_s, p_s)
        rows.append(s.assign(scope=name, brand=s["brand_handle"].map(display)))
    comparison = pd.concat(rows, ignore_index=True)
    with st.container(border=True):
        st.altair_chart(charts.scope_comparison(comparison), width="stretch")
        allc_rates = comparison[comparison["scope"] == "All collected posts"].sort_values("high_or_medium", ascending=False)
        lead = allc_rates.iloc[0] if len(allc_rates) and allc_rates.iloc[0]["high_or_medium"] > 0 else None
        win_hm = int(comparison.loc[comparison["scope"] == "Audit window (60 days)", "high_or_medium"].sum())
        note = (f" Most buying questions sit on **{lead['brand']}** posts ({int(lead['high_or_medium'])} comments)."
                if lead is not None else "")
        st.caption(f"Bars = % of comments with a shopping signal; grey line = 95% confidence interval (cut at the chart edge "
                   f"for tiny samples; hover for the full range). Inside the "
                   f"window: {win_hm} shopping-signal comments.{note}")

    # 4. Coverage timeline
    st.subheader("4 · What was collected, and when")
    with st.container(border=True):
        p_cov = posts_all[posts_all["brand_handle"].isin(sel_brands)]
        st.altair_chart(charts.coverage_timeline(p_cov, window, brand_scale), width="stretch")
        st.caption("Each mark is one post (latest ~20 per brand). Shaded = 60-day audit window. Brands that post rarely "
                   "reach back months or years, which is why window coverage is uneven.")

    # 5. Brand scorecard + seller behaviour
    st.subheader("5 · Competitor scorecard")
    eng = metrics.engagement_summary(posts).assign(brand=lambda d: d["brand_handle"].map(display))
    cap = metrics.caption_signal_summary(posts).assign(brand=lambda d: d["brand_handle"].map(display))
    allp, allc = metrics.scope(posts_all, comments_all, window_only=False, **scope_kwargs)
    intent_all = metrics.intent_summary(allc, allp)[["brand_handle", "high_or_medium_rate_pct", "high"]]
    score = (cov[["brand_handle", "display_name", "posts_collected", "posts_in_window"]]
             .merge(eng[["brand_handle", "median_interactions"]], on="brand_handle", how="left")
             .merge(cap[["brand_handle", "shows_price_pct"]], on="brand_handle", how="left")
             .merge(intent_all, on="brand_handle", how="left"))
    score = score[score["brand_handle"].isin(sel_brands) | (score["posts_collected"] == 0)]
    with st.container(border=True):
        st.markdown("**Brand scorecard** (engagement & captions: current filters · intent: all collected posts)")
        st.dataframe(
            score.drop(columns="brand_handle"), hide_index=True, width="stretch",
            column_config={
                "display_name": "Brand",
                "posts_collected": st.column_config.NumberColumn("Posts collected"),
                "posts_in_window": st.column_config.ProgressColumn("Posts in window", min_value=0, max_value=20, format="%d"),
                "median_interactions": st.column_config.NumberColumn("Median interactions", format="%.0f"),
                "shows_price_pct": st.column_config.ProgressColumn("Captions with ₦ price", min_value=0, max_value=100, format="%.0f%%"),
                "high_or_medium_rate_pct": st.column_config.ProgressColumn("Shopping-signal rate", min_value=0, max_value=10, format="%.1f%%"),
                "high": st.column_config.NumberColumn("Explicit buy requests"),
            })
    with st.container(border=True):
        st.markdown("**What brands do in their captions** (seller-side behaviour, not customer demand)")
        if not cap.empty:
            st.altair_chart(charts.seller_signals(cap), width="stretch")

    # 6. Answer + recommendation
    st.subheader("6 · Answer to the client")
    a1, a2, a3 = st.columns(3)
    with a1.container(border=True):
        st.markdown("#### Which platform should get the budget?")
        st.markdown(":red[**Not answerable from this data.**] Only Instagram was collected, so any percentage split "
                    "would be invented. Ranking platforms needs the same brands & window on each platform.")
    with a2.container(border=True):
        st.markdown("#### Is there buying intent on Instagram comments?")
        st.markdown(f"**Very little.** {k['high_or_medium']} of {k['sampled_comments']:,} comments in scope "
                    f"({hm_rate}) show a shopping signal. Comments are for applause; buying likely moves to DMs and "
                    "WhatsApp, which public scraping can't see.")
    with a3.container(border=True):
        st.markdown("#### What do competitors do differently?")
        if not cap.empty and cap["shows_price_pct"].max() > 0:
            top = cap.sort_values("shows_price_pct", ascending=False).iloc[0]
            st.markdown(f"**{top['brand']}** shows a ₦ price in **{top['shows_price_pct']:.0f}%** of captions; the others "
                        "rarely do. Engagement scale differs >1,000× between brands, so compare within a brand.")
        else:
            st.markdown("No brand in scope shows prices in captions.")

    with st.container(border=True):
        st.markdown("#### ✅ Recommended next step: a 6-week attribution test before any budget split")
        st.markdown(
            "| Week | Action | Measure |\n|---|---|---|\n"
            "| 1 | Give each platform its own WhatsApp click-to-chat link, UTM-tagged site link and discount code | Tracking works end-to-end |\n"
            "| 2–5 | Run equal, small spend on Instagram, TikTok and WhatsApp Status; A/B test showing prices in captions | Conversations, orders, cost per conversation, cost per order |\n"
            "| 6 | Compare results and set the budget split from them | Cost per order by platform, with confidence intervals |")

# ── Purchase intent ─────────────────────────────────────────────────────────
with tabs[1]:
    ib = metrics.intent_summary(comments, posts).assign(brand=lambda d: d["brand_handle"].map(display))
    st.subheader("Intent mix by brand")
    comp = metrics.comment_composition(comments, "brand")
    if comp.empty:
        st.info("No audience comments in scope.")
    else:
        with st.container(border=True):
            st.altair_chart(charts.composition(comp), width="stretch")
    st.subheader("Shopping-signal rate by brand: window vs all posts")
    with st.container(border=True):
        st.altair_chart(charts.scope_comparison(comparison), width="stretch")
    st.subheader("Detail table")
    st.dataframe(ib[["brand", "sampled_comments", "high", "medium", "low", "uncertain", "no_signal", "high_rate_pct",
                     "high_or_medium_rate_pct", "hm_ci_low", "hm_ci_high", "signals_per_100_comments",
                     "high_intent_commenters", "posts_with_high", "posts_with_sampled_comments",
                     "affordability_barrier", "post_purchase_feedback"]], hide_index=True, width="stretch")
    st.caption("Three different things: **high** = comments with a purchase signal; **high_intent_commenters** = distinct "
               "people; transactions = not observable in this data.")
    st.subheader("Platform comparison")
    ip = metrics.intent_summary(comments, posts, "platform")
    st.dataframe(ip[["platform", "sampled_comments", "high", "medium", "high_or_medium_rate_pct", "hm_ci_low", "hm_ci_high"]],
                 hide_index=True, width="stretch")
    if posts["platform"].nunique() < 2:
        st.warning("Only one platform is present, so platforms cannot be compared.")
    st.subheader("Comments (filtered by intent category)")
    view = comments[comments["intent_label"].isin(sel_intents)]
    st.dataframe(view[["brand", "intent_label", "text", "intent_signals", "sentiment_label", "published_date_wat"]]
                 .sort_values("intent_label", key=lambda s: s.map(metrics.INTENT_ORDER.index)),
                 hide_index=True, width="stretch", height=320)

# ── Engagement ──────────────────────────────────────────────────────────────
with tabs[2]:
    e1, e2 = st.columns(2)
    with e1.container(border=True):
        st.markdown("**Interactions per post** (dots = posts, black tick = brand median)")
        if posts["interactions"].notna().any():
            st.altair_chart(charts.interactions_strip(posts, brand_scale), width="stretch")
        st.caption("Log scale: typical posts differ by more than 1,000× between competitors. Hidden likes are excluded, not zero.")
    with e2.container(border=True):
        st.markdown("**Which format performs best, per brand?**")
        fmt = metrics.engagement_summary(posts, ["brand_handle", "post_type"]).assign(brand=lambda d: d["brand_handle"].map(display))
        fmt = fmt.dropna(subset=["median_interactions"])
        if not fmt.empty:
            st.altair_chart(charts.format_mix(fmt, brand_scale), width="stretch")
        st.caption("Compare formats within a brand, not across brands. Small counts per format: hover for n.")
    with st.container(border=True):
        st.markdown("**Posting volume per week**")
        st.altair_chart(charts.weekly_volume(posts, brand_scale), width="stretch")
    eng_t = metrics.engagement_summary(posts).assign(brand=lambda d: d["brand_handle"].map(display))
    st.dataframe(eng_t[["brand", "posts", "posts_likes_known", "median_likes", "mean_likes", "median_comments",
                        "median_interactions", "median_likes_per_1k_followers", "median_video_views"]],
                 hide_index=True, width="stretch")
    st.caption("`median_likes_per_1k_followers` uses manually entered, unverified follower counts. Reference only.")

# ── Posting time ────────────────────────────────────────────────────────────
with tabs[3]:
    t1, t2 = st.columns(2)
    with t1.container(border=True):
        st.markdown("**When competitors post** (Lagos time, WAT = UTC+1)")
        st.altair_chart(charts.posting_heatmap(posts, metrics.WEEKDAYS), width="stretch")
    with t2.container(border=True):
        st.markdown("**Relative performance by weekday** (numbers on bars = posts)")
        wd = metrics.posting_time_summary(posts)
        if not wd.empty:
            st.altair_chart(charts.weekday_performance(wd, metrics.WEEKDAYS), width="stretch")
        st.caption("1.0 = a typical post for that brand. Days with few posts are noise: no schedule recommendation is justified.")

# ── Coverage ────────────────────────────────────────────────────────────────
with tabs[4]:
    with st.container(border=True):
        st.markdown("**Post timeline vs. audit window** (all collected posts)")
        st.altair_chart(charts.coverage_timeline(posts_all, window, brand_scale), width="stretch")
    st.dataframe(metrics.coverage_by_brand(posts_all, comments_all, brand_cfg), hide_index=True, width="stretch")
    st.markdown(
        "- The scraper took the **latest ~20 grid items** per profile, not a date range.\n"
        "- Only about **10 recent comments per post** are returned; `comment_sample_pct` shows how small that is for viral posts.\n"
        "- **Collab posts** are owned by a partner account; use the sidebar toggle to test their effect.\n"
        "- **Hidden likes** (Instagram returns -1) are stored as unknown, never as zero.")
    vpath = PROCESSED_DIR / "validation_report.csv"
    if vpath.exists():
        st.markdown("**Data-quality checks from the last pipeline run**")
        st.dataframe(pd.read_csv(vpath), hide_index=True, width="stretch")

# ── Method ──────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("""
**Purchase-intent categories** (each audience comment; full rules in `docs/intent_taxonomy.md`)

| Category | Meaning | Example |
|---|---|---|
| High | Explicit request about price, ordering, availability, payment or delivery | "How much is this?", "Una dey deliver to Abuja?" |
| Medium | Weaker shopping signal, no clear request | "I need this", "What fabric is this?" |
| Low / product interest | Compliment or interest, no buying request | "This dress is beautiful", "Love it but can't afford it" |
| Uncertain | Possible cue, meaning unclear | "where?", "check your DM" |
| No signal | No purchase cue, negated purchase, post-purchase feedback, or emoji-only | "😍🔥", "I don't want to buy this" |

**Metric definitions**
- *Shopping-signal rate* = (high + medium comments) ÷ audience comments analysed (brand replies excluded), with a 95% Wilson interval.
- *Interactions* = likes + comments per post; unknown if either is hidden.
- *Relative performance* = a post's interactions ÷ that brand's median.
- *Audit window* = 60 days ending at the newest collected post.

**Classifier quality:** `reports/classifier_evaluation.md`. On 150 random real comments, purchase-signal F1 was 0.67
before tuning; labels are not yet human-reviewed and positives are few, so treat it as indicative.

**Stack:** Python (pandas, SQLAlchemy), SQLite/PostgreSQL, Altair, Streamlit, pytest · data via Apify.
""")

# ── Data ────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.dataframe(posts[["brand", "published_date_wat", "post_type", "is_collab", "is_pinned", "likes", "comments_count",
                        "video_views", "caption", "post_url"]], hide_index=True, width="stretch")
    st.download_button("Download filtered posts (CSV)", posts.to_csv(index=False), "posts_filtered.csv", "text/csv")
    st.download_button("Download filtered comments (CSV)", comments.to_csv(index=False), "comments_filtered.csv", "text/csv")

st.caption(f"Pipeline run {manifest.get('run_id', '?')} · code v{manifest.get('code_version', '?')} · "
           f"built by Otuekong Emmanuel")
