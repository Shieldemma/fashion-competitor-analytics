"""Orchestrates Extract -> Validate -> Clean -> Enrich -> Classify -> Store -> Analyze -> Report.

Outputs (all derived, safe to regenerate; raw input is only ever read):
  data/processed/posts.csv, comments.csv           tidy, classified tables
  data/processed/validation_report.csv             data-quality issues
  data/processed/quarantine_*.csv                  rows that could not be used
  data/processed/run_manifest.json                 provenance of this run
  data/processed/analysis/*.csv                    metric tables
  reports/findings_generated.md                    auto-generated findings
  <DATABASE_URL>                                   upserted tables
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import __version__, db, extract, metrics, report, transform, validate
from .config import ANALYSIS_DIR, DEFAULT_DATABASE_URL, PROCESSED_DIR, describe_database_url, get_settings, load_brand_config, log


def build_tables(raw_input: Path, window_days: int, window_end: str | None, brand_cfg: dict | None = None):
    """Extract -> Validate -> Clean/Enrich -> Classify. Pure in-memory; writes nothing."""
    brand_cfg = brand_cfg or load_brand_config()
    registry = {b["brand_handle"] for b in brand_cfg["brands"]}

    extracted = extract.extract(raw_input)
    rep = validate.ValidationReport()
    for issue in extracted.issues:
        rep.add("source", issue["check"], issue["severity"], issue["count"], issue["detail"])

    posts, q_posts = validate.validate_posts(extracted.posts, registry, rep)
    posts, window = transform.transform_posts(posts, brand_cfg, window_days, window_end)
    comments, q_comments = validate.validate_comments(extracted.comments, set(posts["post_id"]), rep)
    comments = transform.transform_comments(comments, posts)
    validate.log_report(rep)
    log.info("Clean/Enrich/Classify: %d posts, %d comments; audit window %s -> %s",
             len(posts), len(comments), window["start_utc"][:10], window["end_utc"][:10])
    return {"posts": posts, "comments": comments, "validation": rep.to_frame(), "quarantine_posts": q_posts,
            "quarantine_comments": q_comments, "window": window, "source": extracted.source, "brand_cfg": brand_cfg}


def analyze(posts: pd.DataFrame, comments: pd.DataFrame, brand_cfg: dict) -> dict[str, pd.DataFrame]:
    p, c = metrics.scope(posts, comments, window_only=True)
    return {
        "coverage_by_brand": metrics.coverage_by_brand(posts, comments, brand_cfg),
        "engagement_by_brand": metrics.engagement_summary(p, "brand_handle"),
        "engagement_by_post_type": metrics.engagement_summary(p, ["brand_handle", "post_type"]),
        "intent_by_brand": metrics.intent_summary(c, p, "brand_handle"),
        "intent_by_platform": metrics.intent_summary(c, p, "platform"),
        "intent_by_post_type": metrics.intent_summary(c, p, "post_type"),
        "caption_signals_by_brand": metrics.caption_signal_summary(p),
        "posting_weekday": metrics.posting_time_summary(p, "published_weekday_wat"),
        "posting_hour": metrics.posting_time_summary(p, "published_hour_wat"),
        "posts_per_day": metrics.posts_per_day(p),
        "sensitivity": metrics.sensitivity(posts, comments),
    }


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)  # atomic: readers never see a half-written file


def run(raw_input: Path | None = None, *, skip_db: bool = False, window_days: int | None = None,
        window_end: str | None = None, database_url: str | None = None) -> dict:
    settings = get_settings()
    raw_input = Path(raw_input or settings.raw_input)
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    log.info("Run %s: input=%s", run_id, raw_input.name)

    t = build_tables(raw_input, window_days or settings.audit_window_days, window_end or settings.audit_window_end)
    posts, comments = t["posts"], t["comments"]
    db_url = database_url or settings.database_url
    is_synthetic = posts["data_source"].astype(str).str.contains("synthetic").any()
    if is_synthetic and not skip_db and db_url == DEFAULT_DATABASE_URL:
        raise SystemExit("Refusing to load SYNTHETIC data into the default warehouse. "
                         "Use --skip-db, or set DATABASE_URL to a separate sample database.")

    _write_csv(posts, PROCESSED_DIR / "posts.csv")
    _write_csv(comments, PROCESSED_DIR / "comments.csv")
    _write_csv(t["validation"], PROCESSED_DIR / "validation_report.csv")
    _write_csv(t["quarantine_posts"], PROCESSED_DIR / "quarantine_posts.csv")
    _write_csv(t["quarantine_comments"], PROCESSED_DIR / "quarantine_comments.csv")

    loaded = None
    if not skip_db:
        engine = db.get_engine(db_url)
        loaded = db.load(engine, t["brand_cfg"], posts, comments, {
            "run_id": run_id, "started_at_utc": started.isoformat(timespec="seconds"),
            "input_file": raw_input.name, "input_sha256": t["source"]["source_sha256"],
            "audit_window_start_utc": t["window"]["start_utc"], "audit_window_end_utc": t["window"]["end_utc"],
            "code_version": __version__,
        })

    tables = analyze(posts, comments, t["brand_cfg"])
    for name, df in tables.items():
        _write_csv(df, ANALYSIS_DIR / f"{name}.csv")

    manifest = {
        "run_id": run_id, "code_version": __version__,
        "started_at_utc": started.isoformat(timespec="seconds"),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": t["source"], "audit_window": t["window"],
        "rows": {"posts": len(posts), "comments": len(comments),
                 "audience_comments": int(comments["is_audience"].sum()) if len(comments) else 0,
                 "quarantined_posts": len(t["quarantine_posts"]), "quarantined_comments": len(t["quarantine_comments"])},
        "database": None if skip_db else describe_database_url(db_url),
        "database_rows_upserted": loaded,
    }
    (PROCESSED_DIR / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report.write_findings(tables, manifest, t["validation"])
    log.info("Run %s complete", run_id)
    return manifest


def load_processed(processed_dir: Path = PROCESSED_DIR) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Read the pipeline outputs back with correct dtypes (used by the dashboard and tests)."""
    posts = pd.read_csv(processed_dir / "posts.csv", keep_default_na=True)
    comments = pd.read_csv(processed_dir / "comments.csv", keep_default_na=True)
    for df in (posts, comments):
        df["published_at_utc"] = pd.to_datetime(df["published_at_utc"], utc=True, errors="coerce", format="mixed")
        for col in df.columns:
            if df[col].dtype == object and set(df[col].dropna().unique()) <= {True, False, "True", "False"}:
                df[col] = df[col].map({True: True, False: False, "True": True, "False": False}).astype("boolean").fillna(False).astype(bool)
    for col in ["likes", "comments_count", "interactions", "video_views", "video_plays", "published_hour_wat"]:
        posts[col] = pd.to_numeric(posts[col], errors="coerce").astype("Int64")
    comments["text"] = comments["text"].fillna("")
    manifest_path = processed_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    return posts, comments, manifest
