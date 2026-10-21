# dashboard/streamlit_app.py
# Run with:  streamlit run dashboard/streamlit_app.py
# Reads the pipeline outputs (data/processed/*.csv) and computes every number
# with fashion_intel.metrics, the same functions behind the report and SQL tests.

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fashion_intel import metrics  # noqa: E402
from fashion_intel.config import PROCESSED_DIR, load_brand_config  # noqa: E402
from fashion_intel.pipeline import load_processed  # noqa: E402

st.set_page_config(page_title="Lagos Fashion Intelligence", page_icon="👗", layout="wide")

# Categorical slots in fixed order (validated: CVD + normal-vision separation pass).
BRAND_SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INTENT_COLORS = {"high": "#1d5fb0", "medium": "#5d9be4", "low": "#b9d3f2", "uncertain": "#9a9890", "no_signal": "#dedcd5"}
INTENT_NAMES = {"high": "High intent", "medium": "Medium intent", "low": "Low / product interest",
                "uncertain": "Uncertain", "no_signal": "No signal"}


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
except Exception as exc:  # show a readable message instead of a stack trace
    st.error(f"Could not read pipeline outputs: {exc}. Re-run `python -m fashion_intel run`.")
    st.stop()

registry = [b["brand_handle"] for b in brand_cfg["brands"]]
display = {b["brand_handle"]: b["display_name"] for b in brand_cfg["brands"]}
brand_color = alt.Scale(domain=[display[h] for h in registry], range=BRAND_SLOTS[: len(registry)])
is_synthetic = posts_all["data_source"].astype(str).str.contains("synthetic").any()

# ── Header & provenance ─────────────────────────────────────────────────────
st.title("Lagos Fashion Competitor Intelligence")
st.caption("Audience purchase-intent signals and engagement for Lagos fashion competitors")

window = manifest.get("audit_window", {})
source = manifest.get("source", {})
if is_synthetic:
    st.error("**SYNTHETIC SAMPLE DATA.** These numbers are generated for demonstration and describe no real brand.")
else:
    platforms = ", ".join(sorted(posts_all["platform"].unique()))
    st.info(
        f"**Data:** public Instagram posts and comments collected with the Apify Instagram Post Scraper "
        f"(file `{source.get('source_file', '?')}`, last modified {str(source.get('file_modified_at_utc', '?'))[:10]}). "
        f"**Platforms collected: {platforms} only.** "
        f"Audit window {str(window.get('start_utc', '?'))[:10]} → {str(window.get('end_utc', '?'))[:10]}. "
        "Purchase intent is inferred from comment text by a rule-based classifier. These are signals, not sales."
    )

# ── Filters ─────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")
brand_options = [h for h in registry if h in set(posts_all["brand_handle"])]
sel_brands = st.sidebar.multiselect("Brand", brand_options, default=brand_options, format_func=lambda h: display.get(h, h))
platform_options = sorted(posts_all["platform"].unique())
sel_platforms = st.sidebar.multiselect("Platform", platform_options, default=platform_options)
window_only = st.sidebar.toggle("Audit window only", value=True, help="Restrict to posts inside the 60-day audit window.")
dates = posts_all["published_date_wat"].dropna()
if window_only:
    dates = posts_all.loc[posts_all["in_audit_window"], "published_date_wat"].dropna()
dmin, dmax = pd.to_datetime(dates.min()).date(), pd.to_datetime(dates.max()).date()
date_range = st.sidebar.date_input("Post date (Lagos time)", value=(dmin, dmax), min_value=dmin, max_value=dmax)
sel_intents = st.sidebar.multiselect("Intent category (comment views)", list(INTENT_NAMES), default=list(INTENT_NAMES),
                                     format_func=INTENT_NAMES.get)
include_collab = st.sidebar.toggle("Include collab posts", value=True,
                                   help="Posts owned by another account but shown on the competitor's grid.")
include_pinned = st.sidebar.toggle("Include pinned posts", value=True)

d_from, d_to = (date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (dmin, dmax))
posts, comments = metrics.scope(posts_all, comments_all, window_only=window_only, include_collab=include_collab,
                                include_pinned=include_pinned, brands=sel_brands, platforms=sel_platforms,
                                date_from=d_from, date_to=d_to)
comments_view = comments[comments["intent_label"].isin(sel_intents)]

if posts.empty:
    st.warning("No posts match these filters. Widen the date range or select more brands.")
    st.stop()

posts = posts.assign(brand=posts["brand_handle"].map(display))
comments = comments.assign(brand=comments["brand_handle"].map(display))
k = metrics.kpis(posts, comments)

# ── KPI row ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Competitors with data", f"{k['brands_with_posts']} of {len(registry)}")
c2.metric("Posts in scope", f"{k['posts']:,}")
c3.metric("Audience comments sampled", f"{k['sampled_comments']:,}")
c4.metric("High-intent comments", f"{k['high']:,}", help="Explicit price/order/availability/delivery/payment requests.")
hm_rate = "–" if pd.isna(k["high_or_medium_rate_pct"]) else f"{k['high_or_medium_rate_pct']:.1f}%"
c5.metric("High + medium intent rate", hm_rate,
          help=f"Share of sampled audience comments. 95% CI {k['hm_ci'][0]}–{k['hm_ci'][1]}%.")
st.caption("The intent-category filter changes the comment tables only. Rates always use all sampled audience comments "
           "in scope as the denominator.")

tabs = st.tabs(["Executive summary", "Purchase intent", "Engagement", "Posting time", "Data coverage", "Method & definitions", "Data"])

# ── Executive summary ───────────────────────────────────────────────────────
with tabs[0]:
    intent_b = metrics.intent_summary(comments, posts)
    st.subheader("What the data says")
    bullets = [
        f"**{k['sampled_comments']:,} audience comments** were sampled on **{k['posts']} posts** from "
        f"**{k['brands_with_posts']} competitors**. **{k['high']}** contain an explicit purchase request and "
        f"**{k['high_or_medium']}** contain any shopping signal (high + medium), a rate of **{hm_rate}** "
        f"(95% CI {k['hm_ci'][0]}–{k['hm_ci'][1]}%).",
    ]
    mix_all = comments["intent_label"].value_counts(normalize=True)
    praise_share = (mix_all.get("low", 0) + mix_all.get("no_signal", 0)) * 100
    if k["sampled_comments"] and praise_share >= 80:
        bullets.append(
            f"**{praise_share:.1f}%** of sampled comments are compliments, emoji reactions, or carry no purchase cue. "
            "On these accounts, public comments look like **a place for applause, not checkout**. Buying conversations "
            "probably move to DMs or WhatsApp, which public scraping cannot see.")
    cap = metrics.caption_signal_summary(posts).assign(brand=lambda d: d["brand_handle"].map(display))
    if not cap.empty:
        top = cap.sort_values("shows_price_pct", ascending=False).iloc[0]
        if top["shows_price_pct"] > 0:
            bullets.append(f"Seller-side: **{top['brand']}** shows prices in **{top['shows_price_pct']:.0f}%** of captions, "
                           "the most of any competitor in scope. That is the brand's copywriting choice, not customer demand.")
    for b in bullets:
        st.markdown(f"- {b}")
    st.subheader("What it cannot tell you")
    st.markdown(
        "- **Which platform to fund.** Only the platforms listed in the banner were collected, so cross-platform "
        "comparison is impossible from this data.\n"
        "- **Sales or ROI.** No transaction, spend, or attribution data exists here. A high-intent comment is a signal, "
        "not a conversion.\n"
        "- **Causation.** Brands differ in audience size, niche, and content. Differences are observational."
    )
    st.subheader("Recommended next step for a Lagos fashion retailer")
    st.markdown(
        "Run a **4–6 week test** with tracked links (UTM) and a unique WhatsApp number or discount code per platform. "
        "Compare **cost per conversation** and **cost per order** across Instagram, TikTok, and WhatsApp before setting a "
        "budget split. Collect TikTok and Facebook data for the same competitors and window to make the platform question answerable."
    )

# ── Purchase intent ─────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Shopping-signal rate by brand")
    st.caption("High + medium comments ÷ sampled audience comments. The line shows the 95% Wilson interval. "
               "Small samples produce wide intervals: do not rank brands whose intervals overlap.")
    ib = metrics.intent_summary(comments, posts).assign(brand=lambda d: d["brand_handle"].map(display))
    if ib.empty:
        st.info("No audience comments in scope.")
    else:
        base = alt.Chart(ib).encode(y=alt.Y("brand:N", sort="-x", title=None))
        bars = base.mark_bar(cornerRadiusEnd=4, height=18).encode(
            x=alt.X("high_or_medium_rate_pct:Q", title="High + medium intent rate (%)"),
            color=alt.Color("brand:N", scale=brand_color, legend=None),
            tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("sampled_comments:Q", title="Comments sampled"),
                     alt.Tooltip("high:Q", title="High"), alt.Tooltip("medium:Q", title="Medium"),
                     alt.Tooltip("high_or_medium_rate_pct:Q", title="Rate %", format=".2f"),
                     alt.Tooltip("hm_ci_low:Q", title="CI low %"), alt.Tooltip("hm_ci_high:Q", title="CI high %")])
        ci = base.mark_rule(strokeWidth=2, color="#52514e").encode(x="hm_ci_low:Q", x2="hm_ci_high:Q")
        st.altair_chart((bars + ci).properties(height=60 + 34 * len(ib)), width="stretch")

        st.subheader("Intent mix by brand")
        mix = ib.melt(id_vars=["brand", "sampled_comments"], value_vars=list(INTENT_NAMES), var_name="intent", value_name="comments")
        mix["intent_name"] = mix["intent"].map(INTENT_NAMES)
        mix["share_pct"] = mix["comments"] / mix["sampled_comments"] * 100
        order = list(INTENT_NAMES.values())
        stacked = alt.Chart(mix).mark_bar(height=18, stroke="white", strokeWidth=2).encode(
            y=alt.Y("brand:N", title=None),
            x=alt.X("share_pct:Q", title="Share of sampled comments (%)", stack="zero"),
            color=alt.Color("intent_name:N", scale=alt.Scale(domain=order, range=[INTENT_COLORS[i] for i in INTENT_NAMES]),
                            legend=alt.Legend(title=None, orient="top")),
            order=alt.Order("intent_order:Q"),
            tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("intent_name:N", title="Category"),
                     alt.Tooltip("comments:Q", title="Comments"), alt.Tooltip("share_pct:Q", title="Share %", format=".1f")],
        ).transform_calculate(intent_order=f"indexof({order}, datum.intent_name)")
        st.altair_chart(stacked.properties(height=60 + 34 * len(ib)), width="stretch")

        st.dataframe(ib[["brand", "sampled_comments", "high", "medium", "low", "uncertain", "no_signal", "high_rate_pct",
                         "high_or_medium_rate_pct", "hm_ci_low", "hm_ci_high", "signals_per_100_comments",
                         "high_intent_commenters", "posts_with_high", "posts_with_sampled_comments",
                         "affordability_barrier", "post_purchase_feedback"]], hide_index=True, width="stretch")
        st.caption("Three different things: **high** = comments with a purchase signal; **high_intent_commenters** = distinct "
                   "people expressing it; transactions = not observable in this data.")

    st.subheader("Platform comparison")
    ip = metrics.intent_summary(comments, posts, "platform")
    st.dataframe(ip[["platform", "sampled_comments", "high", "medium", "high_or_medium_rate_pct", "hm_ci_low", "hm_ci_high"]],
                 hide_index=True, width="stretch")
    if posts["platform"].nunique() < 2:
        st.warning("Only one platform is present, so platforms cannot be compared. Collect a second platform for the same brands and window.")

    st.subheader("Comments (filtered by intent category)")
    show = comments_view.assign(brand=comments_view["brand_handle"].map(display))
    st.dataframe(show[["brand", "intent_label", "text", "intent_signals", "sentiment_label", "published_date_wat"]]
                 .sort_values("intent_label", key=lambda s: s.map(metrics.INTENT_ORDER.index)),
                 hide_index=True, width="stretch", height=320)

# ── Engagement ──────────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Interactions per post (likes + comments)")
    st.caption("Each dot is one post. Log scale: typical posts differ by more than 1,000× between competitors. Posts with hidden likes are excluded, not counted as zero.")
    pe = posts.dropna(subset=["interactions"]).assign(interactions=lambda d: d["interactions"].astype(float))
    if pe.empty:
        st.info("No posts with known interactions in scope.")
    else:
        dots = alt.Chart(pe).mark_circle(size=90, opacity=0.85, stroke="white", strokeWidth=2).encode(
            x=alt.X("interactions:Q", scale=alt.Scale(type="log"), title="Interactions per post (log scale)"),
            y=alt.Y("brand:N", title=None),
            color=alt.Color("brand:N", scale=brand_color, legend=None),
            tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("published_date_wat:N", title="Date"),
                     alt.Tooltip("post_type:N", title="Format"), alt.Tooltip("likes:Q", title="Likes", format=","),
                     alt.Tooltip("comments_count:Q", title="Comments", format=","), alt.Tooltip("is_collab:N", title="Collab"),
                     alt.Tooltip("post_url:N", title="URL")])
        st.altair_chart(dots.properties(height=60 + 40 * pe["brand"].nunique()), width="stretch")
    eng = metrics.engagement_summary(posts).assign(brand=lambda d: d["brand_handle"].map(display))
    st.dataframe(eng[["brand", "posts", "posts_likes_known", "median_likes", "mean_likes", "median_comments",
                      "median_interactions", "median_likes_per_1k_followers", "median_video_views"]],
                 hide_index=True, width="stretch")
    st.caption("`median_likes_per_1k_followers` uses manually entered, unverified follower counts. Treat it as reference only.")

    st.subheader("Seller-side caption behaviour")
    cap = metrics.caption_signal_summary(posts).assign(brand=lambda d: d["brand_handle"].map(display))
    st.dataframe(cap[["brand", "posts", "shows_price_pct", "call_to_action_pct", "launch_or_restock_pct"]], hide_index=True, width="stretch")

    st.subheader("Posts per week")
    weekly = posts.dropna(subset=["published_at_utc"]).assign(
        week=lambda d: pd.to_datetime(d["published_date_wat"]).dt.to_period("W-SUN").dt.start_time)
    weekly = weekly.groupby(["week", "brand"]).size().rename("posts").reset_index()
    vol = alt.Chart(weekly).mark_bar(stroke="white", strokeWidth=2).encode(
        x=alt.X("week:T", title="Week starting (Lagos time)"), y=alt.Y("posts:Q", title="Posts"),
        color=alt.Color("brand:N", scale=brand_color, legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("week:T", title="Week"), alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("posts:Q", title="Posts")])
    st.altair_chart(vol.properties(height=260), width="stretch")

# ── Posting time ────────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("When competitors post (Lagos time, WAT = UTC+1)")
    heat = posts.dropna(subset=["published_hour_wat"]).groupby(["published_weekday_wat", "published_hour_wat"]).size().rename("posts").reset_index()
    hm = alt.Chart(heat).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("published_hour_wat:O", title="Hour of day (WAT)"),
        y=alt.Y("published_weekday_wat:N", sort=metrics.WEEKDAYS, title=None),
        color=alt.Color("posts:Q", scale=alt.Scale(scheme="blues"), legend=alt.Legend(title="Posts")),
        tooltip=[alt.Tooltip("published_weekday_wat:N", title="Day"), alt.Tooltip("published_hour_wat:O", title="Hour"),
                 alt.Tooltip("posts:Q", title="Posts")])
    st.altair_chart(hm.properties(height=260), width="stretch")

    st.subheader("Relative performance by weekday")
    st.caption("1.0 = a typical post for that brand (interactions ÷ the brand's median). Buckets with only a few posts are noise.")
    wd = metrics.posting_time_summary(posts)
    if not wd.empty:
        bar = alt.Chart(wd).mark_bar(cornerRadiusEnd=4, color=BRAND_SLOTS[0]).encode(
            x=alt.X("published_weekday_wat:N", sort=metrics.WEEKDAYS, title=None),
            y=alt.Y("median_relative_performance:Q", title="Median relative performance"),
            tooltip=[alt.Tooltip("published_weekday_wat:N", title="Day"), alt.Tooltip("posts:Q", title="Posts"),
                     alt.Tooltip("brands:Q", title="Brands"), alt.Tooltip("median_relative_performance:Q", title="Median ×")])
        rule = alt.Chart(pd.DataFrame({"y": [1.0]})).mark_rule(strokeDash=[4, 4], color="#8a8983").encode(y="y:Q")
        st.altair_chart((bar + rule).properties(height=260), width="stretch")
        st.dataframe(wd, hide_index=True, width="stretch")

# ── Coverage ────────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("What was actually collected (all posts, before filters)")
    cov = metrics.coverage_by_brand(posts_all, comments_all, brand_cfg)
    st.dataframe(cov, hide_index=True, width="stretch")
    st.markdown(
        "- The scraper took the **latest ~20 grid items** per profile, not a date range. Some brands post rarely, "
        "so their 20 posts span months and only a few fall in the window.\n"
        "- Only about **10 recent comments per post** are returned. `comment_sample_pct` shows how small that sample is "
        "for viral posts.\n"
        "- **Collab posts** are shown on a competitor's grid but owned by another account. Use the sidebar toggle to "
        "test whether they change the picture.\n"
        "- **Hidden likes** (Instagram returns -1) are stored as unknown, never as zero."
    )
    vpath = PROCESSED_DIR / "validation_report.csv"
    if vpath.exists():
        st.subheader("Data-quality checks from the last pipeline run")
        st.dataframe(pd.read_csv(vpath), hide_index=True, width="stretch")

# ── Method ──────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("""
**Purchase-intent categories** (applied to each audience comment, see `docs/intent_taxonomy.md`)

| Category | Meaning | Example |
|---|---|---|
| High | Explicit request about price, ordering, availability, payment or delivery | "How much is this?", "Una dey deliver to Abuja?" |
| Medium | Weaker shopping signal, no clear request | "I need this", "What fabric is this?" |
| Low / product interest | Compliment or interest, no buying request | "This dress is beautiful", "Love it but can't afford it" |
| Uncertain | Possible cue, meaning unclear | "where?", "check your DM" without context |
| No signal | No purchase cue, negated purchase, post-purchase feedback, or emoji-only | "😍🔥", "I don't want to buy this" |

**Metric definitions**
- *High + medium intent rate* = (high + medium comments) ÷ sampled audience comments. Brand and collaborator replies are excluded.
- *Interactions* = likes + comments for a post. Unknown if either is hidden.
- *Relative performance* = a post's interactions ÷ that brand's median interactions.
- *Audit window* = 60 days ending at the newest collected post.

**Classifier quality:** see `reports/classifier_evaluation.md`. Labels are not yet human-reviewed, and the
high/medium support is in single digits, so treat precision and recall as rough indications.
""")

# ── Data ────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.dataframe(posts[["brand", "published_date_wat", "post_type", "is_collab", "is_pinned", "likes", "comments_count",
                        "video_views", "caption", "post_url"]], hide_index=True, width="stretch")
    st.download_button("Download filtered posts (CSV)", posts.to_csv(index=False), "posts_filtered.csv", "text/csv")
    st.download_button("Download filtered comments (CSV)", comments_view.to_csv(index=False), "comments_filtered.csv", "text/csv")

st.caption(f"Pipeline run {manifest.get('run_id', '?')} · code v{manifest.get('code_version', '?')}")
