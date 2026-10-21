import math

import pandas as pd
import pytest

from fashion_intel import metrics


def test_safe_rate_zero_and_unknown_denominators():
    assert math.isnan(metrics.safe_rate(3, 0))
    assert math.isnan(metrics.safe_rate(3, None))
    assert math.isnan(metrics.safe_rate(3, float("nan")))
    assert metrics.safe_rate(1, 4) == 25.0


def test_wilson_interval():
    assert all(math.isnan(v) for v in metrics.wilson_interval(0, 0))
    lo, hi = metrics.wilson_interval(0, 10)
    assert lo == 0 and 25 < hi < 35            # zero successes still has real uncertainty
    lo, hi = metrics.wilson_interval(50, 100)
    assert lo < 50 < hi


def _posts():
    return pd.DataFrame({
        "post_id": ["p1", "p2", "p3", "p4"],
        "brand_handle": ["a", "a", "b", "b"],
        "platform": ["instagram"] * 4,
        "brand_in_registry": [True] * 4,
        "in_audit_window": [True, True, True, False],
        "is_collab": [False, True, False, False],
        "is_pinned": [False, False, False, True],
        "published_date_wat": ["2026-05-01", "2026-05-02", "2026-05-03", "2025-01-01"],
        "published_weekday_wat": ["Friday", "Saturday", "Sunday", "Wednesday"],
        "likes": pd.array([100, None, 10, 5], dtype="Int64"),
        "likes_hidden": [False, True, False, False],
        "comments_count": pd.array([10, 5, 1, 1], dtype="Int64"),
        "interactions": pd.array([110, None, 11, 6], dtype="Int64"),
        "likes_per_1k_followers": [10.0, None, 1.0, 0.5],
        "video_views": pd.array([None, None, None, None], dtype="Int64"),
        "caption_shows_price": [True, False, False, False],
        "caption_call_to_action": [True, True, False, False],
        "caption_launch_or_restock": [False, False, False, False],
    })


def _comments():
    return pd.DataFrame({
        "comment_id": ["c1", "c2", "c3", "c4", "c5", "c6"],
        "post_id": ["p1", "p1", "p2", "p3", "p1", "p4"],
        "commenter_id": ["u1", "u2", "u1", "u3", "brand", "u4"],
        "is_audience": [True, True, True, True, False, True],
        "intent_label": ["high", "low", "high", "medium", "high", "high"],
        "intent_signal_count": [1, 0, 2, 1, 1, 1],
        "intent_reason": ["x"] * 6,
        "affordability_barrier": [False] * 6,
        "post_purchase_feedback": [False] * 6,
    })


def test_scope_excludes_brand_replies_and_out_of_window():
    p, c = metrics.scope(_posts(), _comments())
    assert set(p["post_id"]) == {"p1", "p2", "p3"}
    assert set(c["comment_id"]) == {"c1", "c2", "c3", "c4"}   # c5 = brand reply, c6 = out of window


def test_scope_date_filter_inclusive():
    p, _ = metrics.scope(_posts(), _comments(), date_from="2026-05-02", date_to="2026-05-02")
    assert p["post_id"].tolist() == ["p2"]


def test_intent_summary_counts_and_denominators():
    p, c = metrics.scope(_posts(), _comments())
    s = metrics.intent_summary(c, p).set_index("brand_handle")
    a = s.loc["a"]
    assert a["sampled_comments"] == 3 and a["high"] == 2 and a["low"] == 1
    assert a["high_rate_pct"] == pytest.approx(66.67, abs=0.01)
    assert a["high_intent_commenters"] == 1          # u1 twice = one person
    assert a["posts_with_high"] == 2 and a["posts_with_sampled_comments"] == 2
    assert s.loc["b", "high_or_medium_rate_pct"] == 100.0


def test_intent_summary_empty_input():
    out = metrics.intent_summary(_comments().iloc[0:0], _posts())
    assert out.empty and "high_rate_pct" in out.columns


def test_engagement_excludes_unknown_likes():
    p, _ = metrics.scope(_posts(), _comments())
    e = metrics.engagement_summary(p).set_index("brand_handle")
    assert e.loc["a", "posts"] == 2 and e.loc["a", "posts_likes_known"] == 1
    assert e.loc["a", "median_likes"] == 100.0       # the hidden-likes post is not a zero


def test_coverage_lists_brand_without_data():
    cfg = {"brands": [{"brand_handle": "a", "display_name": "A"}, {"brand_handle": "zzz", "display_name": "Z"}]}
    cov = metrics.coverage_by_brand(_posts(), _comments(), cfg).set_index("brand_handle")
    assert cov.loc["zzz", "posts_collected"] == 0 and cov.loc["zzz", "status"] == "no data collected"
    assert cov.loc["a", "collab_posts"] == 1


def test_posting_time_is_relative_within_brand():
    p, _ = metrics.scope(_posts(), _comments(), window_only=False)
    out = metrics.posting_time_summary(p).set_index("published_weekday_wat")
    assert out.loc["Friday", "median_relative_performance"] == 1.0   # brand a's only known post
    assert list(out.index) == ["Wednesday", "Friday", "Sunday"]      # calendar order, not alphabetical


def test_sensitivity_has_all_scenarios():
    s = metrics.sensitivity(_posts(), _comments())
    assert set(s["scenario"]) == set(metrics.SCENARIOS) | {"window_text_comments_only"}


def test_scope_empty_selection_means_nothing_not_everything():
    p, c = metrics.scope(_posts(), _comments(), brands=[])
    assert p.empty and c.empty
    p, _ = metrics.scope(_posts(), _comments(), brands=None)
    assert not p.empty


def test_funnel_and_composition():
    c = _comments().assign(intent_reason=["x", "no_text_emoji_or_symbols", "x", "x", "x", "x"],
                           brand_handle=["a", "a", "a", "b", "a", "b"])
    c = c[c["is_audience"]]
    f = metrics.intent_funnel(c).set_index("step")["count"]
    assert f["Audience comments sampled"] == 5
    assert f["Contain words (not just emoji/tags)"] == 4
    assert f["Explicit purchase request"] == 3 and f["Distinct people asking to buy"] == 2
    assert pd.isna(f["Verified purchases"])            # never claimed
    comp = metrics.comment_composition(c)
    assert comp.groupby("brand_handle")["share_pct"].sum().round().eq(100).all()
    assert set(comp["category"]) <= set(metrics.COMPOSITION_ORDER)
