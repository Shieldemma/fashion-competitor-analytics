"""Store: idempotent loading into SQLite (default) or PostgreSQL.

- Works with any SQLAlchemy URL in DATABASE_URL; defaults to a local SQLite
  file so the project runs with zero setup.
- Uses new table names (competitor_brands, social_posts, audience_comments,
  pipeline_runs), so it never alters the legacy `brands`/`posts` tables.
- Upserts on stable natural keys: re-running the pipeline updates rows in
  place instead of duplicating them. One transaction per load: if anything
  fails, nothing is written.
- Never drops or truncates tables.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, MetaData, String, Table, Text,
                        create_engine, event, text)
from sqlalchemy.engine import Engine

from .config import WAREHOUSE_DIR, describe_database_url, log

metadata = MetaData()

competitor_brands = Table(
    "competitor_brands", metadata,
    Column("brand_handle", String(100), primary_key=True),
    Column("display_name", String(200)),
    Column("platform", String(30)),
    Column("in_registry", Boolean, nullable=False),
    Column("follower_count_reference", Integer, nullable=True),
    Column("follower_source", Text),
    Column("follower_as_of", String(10)),
)

social_posts = Table(
    "social_posts", metadata,
    Column("post_id", String(120), primary_key=True),
    Column("platform", String(30), nullable=False),
    Column("brand_handle", String(100), ForeignKey("competitor_brands.brand_handle"), nullable=False),
    Column("owner_username", String(100)),
    Column("is_collab", Boolean, nullable=False),
    Column("is_pinned", Boolean, nullable=False),
    Column("post_url", Text, nullable=False, unique=True),
    Column("shortcode", String(60)),
    Column("post_type", String(30)),
    Column("caption", Text),
    Column("published_at_utc", DateTime(timezone=True)),
    Column("published_date_wat", String(10)),
    Column("published_hour_wat", Integer),
    Column("published_weekday_wat", String(10)),
    Column("in_audit_window", Boolean, nullable=False),
    Column("likes", Integer, nullable=True),            # NULL = hidden/unknown, never 0
    Column("likes_hidden", Boolean, nullable=False),
    Column("comments_count", Integer, nullable=True),
    Column("interactions", Integer, nullable=True),     # likes + comments, NULL if either unknown
    Column("video_views", Integer, nullable=True),
    Column("video_plays", Integer, nullable=True),
    Column("likes_per_1k_followers", Float, nullable=True),
    Column("caption_shows_price", Boolean),
    Column("caption_call_to_action", Boolean),
    Column("caption_launch_or_restock", Boolean),
    Column("data_source", String(60), nullable=False),
    Column("source_file", Text, nullable=False),
    Column("source_sha256", String(64), nullable=False),
    Column("source_row", Integer),
    Column("extracted_at_utc", String(40)),
    Column("loaded_by_run_id", String(40)),
)
Index("ix_posts_brand_date", social_posts.c.brand_handle, social_posts.c.published_date_wat)
Index("ix_posts_platform", social_posts.c.platform)

audience_comments = Table(
    "audience_comments", metadata,
    Column("comment_id", String(160), primary_key=True),
    Column("post_id", String(120), ForeignKey("social_posts.post_id"), nullable=False),
    Column("brand_handle", String(100), nullable=False),
    Column("parent_comment_id", String(160)),
    Column("is_reply", Boolean, nullable=False),
    Column("commenter_id", String(40)),                  # pseudonymised, never the real handle
    Column("is_account_reply", Boolean, nullable=False),
    Column("is_audience", Boolean, nullable=False),
    Column("text", Text),
    Column("published_at_utc", DateTime(timezone=True)),
    Column("published_date_wat", String(10)),
    Column("comment_likes", Integer),
    Column("intent_label", String(20), nullable=False),
    Column("intent_signals", Text),
    Column("intent_signal_count", Integer, nullable=False),
    Column("intent_negated", Boolean, nullable=False),
    Column("affordability_barrier", Boolean, nullable=False),
    Column("post_purchase_feedback", Boolean, nullable=False),
    Column("sentiment_polarity", Float),
    Column("sentiment_label", String(10)),
    Column("source_sha256", String(64), nullable=False),
    Column("loaded_by_run_id", String(40)),
)
Index("ix_comments_post", audience_comments.c.post_id)
Index("ix_comments_brand_intent", audience_comments.c.brand_handle, audience_comments.c.intent_label)

pipeline_runs = Table(
    "pipeline_runs", metadata,
    Column("run_id", String(40), primary_key=True),
    Column("started_at_utc", String(40), nullable=False),
    Column("finished_at_utc", String(40)),
    Column("status", String(20), nullable=False),
    Column("input_file", Text),
    Column("input_sha256", String(64)),
    Column("posts_loaded", Integer),
    Column("comments_loaded", Integer),
    Column("audit_window_start_utc", String(40)),
    Column("audit_window_end_utc", String(40)),
    Column("code_version", String(20)),
)


def get_engine(url: str) -> Engine:
    if url.startswith("sqlite:///") and ":memory:" not in url:
        WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, future=True, pool_pre_ping=True)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_conn, _record):  # SQLite ignores FKs unless asked
            dbapi_conn.execute("PRAGMA foreign_keys = ON")
    log.info("Store: using %s", describe_database_url(url))
    return engine


def create_schema(engine: Engine) -> None:
    """CREATE TABLE IF NOT EXISTS for every table. Non-destructive."""
    metadata.create_all(engine, checkfirst=True)


def _records(df: pd.DataFrame, table: Table) -> list[dict]:
    cols = [c.name for c in table.columns if c.name in df.columns]
    out = df[cols].astype(object).where(df[cols].notna(), None)
    records = out.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.to_pydatetime()
    return records


def _upsert(conn, table: Table, records: list[dict], chunk: int = 500) -> int:
    if not records:
        return 0
    dialect = conn.engine.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise NotImplementedError(f"Upsert not implemented for {dialect}")
    pk = [c.name for c in table.primary_key.columns]
    for i in range(0, len(records), chunk):
        stmt = insert(table).values(records[i:i + chunk])
        update = {c.name: stmt.excluded[c.name] for c in table.columns if c.name not in pk}
        conn.execute(stmt.on_conflict_do_update(index_elements=pk, set_=update))
    return len(records)


def load(engine: Engine, brand_cfg: dict, posts: pd.DataFrame, comments: pd.DataFrame, run: dict) -> dict:
    """Upsert everything in a single transaction. Returns row counts."""
    create_schema(engine)
    brands = pd.DataFrame(brand_cfg["brands"]).rename(columns={"follower_count": "follower_count_reference"})
    brands["in_registry"] = True
    extra = sorted(set(posts["brand_handle"]) - set(brands["brand_handle"]))
    if extra:
        brands = pd.concat([brands, pd.DataFrame({"brand_handle": extra, "display_name": extra, "in_registry": False})])
    posts = posts.assign(loaded_by_run_id=run["run_id"])
    comments = comments.assign(loaded_by_run_id=run["run_id"])

    with engine.begin() as conn:  # commit on success, rollback on any error
        conn.execute(pipeline_runs.insert().values(**{**run, "status": "running"}))
        n_brands = _upsert(conn, competitor_brands, _records(brands, competitor_brands))
        n_posts = _upsert(conn, social_posts, _records(posts, social_posts))
        n_comments = _upsert(conn, audience_comments, _records(comments, audience_comments))
        conn.execute(pipeline_runs.update().where(pipeline_runs.c.run_id == run["run_id"]).values(
            status="success", posts_loaded=n_posts, comments_loaded=n_comments,
            finished_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds")))
    log.info("Store: upserted %d brands, %d posts, %d comments", n_brands, n_posts, n_comments)
    return {"brands": n_brands, "posts": n_posts, "comments": n_comments}


def run_sql_file(engine: Engine, path, params: dict | None = None) -> pd.DataFrame:
    """Run one read-only analytical query from sql/ with bound parameters."""
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
