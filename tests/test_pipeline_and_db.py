import hashlib
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from fashion_intel import db, extract, metrics, pipeline, validate
from fashion_intel.config import DEFAULT_RAW_INPUT, SQL_DIR, load_brand_config


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def tables(apify_csv, brand_cfg):
    return pipeline.build_tables(apify_csv, 60, None, brand_cfg)


def test_raw_file_is_never_modified(apify_csv, brand_cfg):
    before = _sha(apify_csv)
    pipeline.build_tables(apify_csv, 60, None, brand_cfg)
    assert _sha(apify_csv) == before


def test_extract_attributes_posts_to_scraped_profile(tables):
    posts = tables["posts"].set_index("post_id")
    assert posts.loc["instagram:B1", "brand_handle"] == "beta"
    assert posts.loc["instagram:B1", "owner_username"] == "partner_account"
    assert bool(posts.loc["instagram:B1", "is_collab"])
    assert posts.loc["instagram:B1", "likes"] == 1200           # "1.2K"


def test_duplicates_removed_and_hidden_likes_are_null(tables):
    posts = tables["posts"]
    assert posts["post_id"].is_unique and len(posts) == 5
    a2 = posts.set_index("post_id").loc["instagram:A2"]
    assert pd.isna(a2["likes"]) and bool(a2["likes_hidden"]) and pd.isna(a2["interactions"])
    assert (posts["likes"].dropna() >= 0).all()


def test_follower_count_unknown_is_not_invented(tables):
    beta = tables["posts"][tables["posts"]["brand_handle"] == "beta"]
    assert beta["follower_count_reference"].isna().all()
    assert beta["likes_per_1k_followers"].isna().all()


def test_error_row_and_malformed_date_are_reported(tables):
    v = tables["validation"].set_index("check")
    assert "scraper_error_row" in v.index and "gamma" in v.loc["scraper_error_row", "detail"]
    b3 = tables["posts"].set_index("post_id").loc["instagram:B3"]
    assert pd.isna(b3["published_at_utc"]) and not b3["in_audit_window"]


def test_window_and_pinned(tables):
    posts = tables["posts"].set_index("post_id")
    assert bool(posts.loc["instagram:B2", "is_pinned"]) and not posts.loc["instagram:B2", "in_audit_window"]
    assert posts.loc["instagram:A1", "in_audit_window"]


def test_comments_classified_and_brand_replies_flagged(tables):
    c = tables["comments"].set_index("comment_id")
    assert c.loc["instagram:c:c1", "intent_label"] == "high"
    assert c.loc["instagram:c:c4", "intent_label"] == "no_signal"
    reply = c.loc["instagram:c:c3"]
    assert reply["is_reply"] and reply["is_account_reply"] and not reply["is_audience"]
    assert c["commenter_id"].dropna().str.startswith("user_").all()     # no raw handles
    assert c.index.is_unique


def test_missing_required_column_is_a_schema_error(brand_cfg):
    df = pd.DataFrame({"post_id": ["x"]})
    with pytest.raises(validate.SchemaError):
        validate.validate_posts(df, {"alpha"}, validate.ValidationReport())


def test_unknown_format_rejected(tmp_path):
    p = tmp_path / "x.csv"
    pd.DataFrame({"foo": [1]}).to_csv(p, index=False)
    with pytest.raises(ValueError, match="Unrecognised input format"):
        extract.extract(p)


def test_generic_posts_csv_supported(tmp_path):
    p = tmp_path / "generic.csv"
    pd.DataFrame({"brand": ["@Alpha"], "platform": ["IG"], "post_url": ["instagram.com/p/XYZ"],
                  "caption": ["Price?"], "likes": ["2.3K"], "post_date": ["2026-05-01T10:00:00"]}).to_csv(p, index=False)
    out = extract.extract(p)
    row = out.posts.iloc[0]
    assert row["brand_handle"] == "alpha" and row["platform"] == "instagram" and row["likes"] == 2300
    assert row["post_id"] == "instagram:XYZ"


# ── Database ────────────────────────────────────────────────────────────────

def _run(i=1):
    return {"run_id": f"test-run-{i}", "started_at_utc": "2026-01-01T00:00:00+00:00", "input_file": "t.csv",
            "input_sha256": "0" * 64, "audit_window_start_utc": "", "audit_window_end_utc": "", "code_version": "test"}


@pytest.fixture
def engine(tmp_path):
    return db.get_engine(f"sqlite:///{tmp_path / 'test.db'}")


def _count(engine, table):
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def test_load_is_idempotent(engine, tables, brand_cfg):
    db.load(engine, brand_cfg, tables["posts"], tables["comments"], _run(1))
    first = (_count(engine, "social_posts"), _count(engine, "audience_comments"))
    db.load(engine, brand_cfg, tables["posts"], tables["comments"], _run(2))
    assert (_count(engine, "social_posts"), _count(engine, "audience_comments")) == first
    assert _count(engine, "pipeline_runs") == 2


def test_failed_load_rolls_back_everything(engine, tables, brand_cfg):
    bad_posts = tables["posts"].copy()
    bad_posts.loc[0, "platform"] = None           # violates NOT NULL
    with pytest.raises(IntegrityError):
        db.load(engine, brand_cfg, bad_posts, tables["comments"], _run(1))
    assert _count(engine, "social_posts") == 0
    assert _count(engine, "pipeline_runs") == 0


def test_foreign_keys_enforced(engine, tables, brand_cfg):
    orphan = tables["comments"].head(1).assign(post_id="instagram:DOES_NOT_EXIST")
    with pytest.raises(IntegrityError):
        db.load(engine, brand_cfg, tables["posts"], orphan, _run(1))


def _assert_sql_matches_python(engine, posts, comments, brand_cfg):
    db.load(engine, brand_cfg, posts, comments, _run(1))
    p, c = metrics.scope(posts, comments, window_only=True)

    sql_intent = db.run_sql_file(engine, SQL_DIR / "intent_analysis.sql", {"include_all": 0}).set_index("brand_handle")
    py_intent = metrics.intent_summary(c, p).set_index("brand_handle")
    assert set(sql_intent.index) == set(py_intent.index)
    for col in ["sampled_comments", "high", "medium", "low", "uncertain", "no_signal",
                "high_intent_commenters", "posts_with_high"]:
        assert (sql_intent[col].astype(int) == py_intent.loc[sql_intent.index, col].astype(int)).all(), col
    for col in ["high_rate_pct", "high_or_medium_rate_pct", "signals_per_100_comments"]:
        assert sql_intent[col].astype(float).values == pytest.approx(py_intent.loc[sql_intent.index, col].astype(float).values, abs=0.01), col

    sql_top = db.run_sql_file(engine, SQL_DIR / "top_brands.sql", {"include_all": 0}).set_index("brand_handle")
    py_eng = metrics.engagement_summary(p).set_index("brand_handle")
    assert (sql_top["posts"] == py_eng.loc[sql_top.index, "posts"]).all()
    assert (sql_top["posts_likes_known"] == py_eng.loc[sql_top.index, "posts_likes_known"]).all()
    py_avg = p.groupby("brand_handle")["likes"].mean().round(1)
    assert sql_top["avg_likes"].astype(float).values == pytest.approx(py_avg.loc[sql_top.index].astype(float).values, abs=0.05)

    for f in ["engagement_analysis.sql", "posting_times.sql", "platform_intent.sql", "data_coverage.sql"]:
        db.run_sql_file(engine, SQL_DIR / f, {"include_all": 0})     # every query runs


def test_sql_matches_python_on_fixture(engine, tables, brand_cfg):
    _assert_sql_matches_python(engine, tables["posts"], tables["comments"], brand_cfg)


@pytest.mark.skipif(not DEFAULT_RAW_INPUT.exists(), reason="real Apify export not present")
def test_real_data_invariants_and_sql_agreement(engine):
    cfg = load_brand_config()
    t = pipeline.build_tables(DEFAULT_RAW_INPUT, 60, None, cfg)
    posts, comments = t["posts"], t["comments"]
    assert set(posts["brand_handle"]) == {"veekeejames_official", "ashluxe", "wflsncrm", "zivalagos"}
    assert posts["post_id"].is_unique and posts["platform"].eq("instagram").all()
    assert (posts["likes"].dropna() >= 0).all() and posts["likes_hidden"].sum() == 4
    assert comments["post_id"].isin(posts["post_id"]).all()
    _assert_sql_matches_python(engine, posts, comments, cfg)


def test_synthetic_data_cannot_enter_default_warehouse(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    p = tmp_path / "synthetic.csv"
    pd.DataFrame({"brand": ["alpha"], "platform": ["instagram"], "post_url": ["https://www.instagram.com/p/S1/"],
                  "caption": ["x"], "likes": [1], "post_date": ["2026-05-01T10:00:00Z"],
                  "data_source": ["synthetic_sample"]}).to_csv(p, index=False)
    with pytest.raises(SystemExit, match="SYNTHETIC"):
        pipeline.run(p)
