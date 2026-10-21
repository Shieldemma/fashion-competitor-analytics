"""Command line entry point.

  python -m fashion_intel run                 # full pipeline (default DB: local SQLite)
  python -m fashion_intel run --skip-db       # everything except the database load
  python -m fashion_intel evaluate            # classifier precision / recall / F1
  python -m fashion_intel classify "How much?"
  python -m fashion_intel schema              # print PostgreSQL DDL
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import setup_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fashion_intel", description="Lagos fashion competitor intelligence pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="run the full pipeline")
    run_p.add_argument("--input", type=Path, help="raw export (default: RAW_INPUT_PATH or data/raw/apify_raw.csv)")
    run_p.add_argument("--skip-db", action="store_true", help="do not write to the database")
    run_p.add_argument("--window-days", type=int, help="audit window length (default 60)")
    run_p.add_argument("--window-end", help="audit window end date YYYY-MM-DD (default: newest post)")

    sub.add_parser("evaluate", help="evaluate the intent classifier on the labelled set")
    cls_p = sub.add_parser("classify", help="classify one or more texts")
    cls_p.add_argument("texts", nargs="+")
    sub.add_parser("schema", help="print the PostgreSQL DDL for the warehouse tables")

    args = parser.parse_args(argv)

    if args.command == "run":
        log_path = setup_logging("pipeline")
        from .pipeline import run
        manifest = run(args.input, skip_db=args.skip_db, window_days=args.window_days, window_end=args.window_end)
        print(f"\nDone. Run {manifest['run_id']}: {manifest['rows']['posts']} posts, "
              f"{manifest['rows']['audience_comments']} audience comments. Log: {log_path}")
    elif args.command == "evaluate":
        setup_logging("evaluate")
        from .evaluate import main as evaluate_main
        evaluate_main()
    elif args.command == "classify":
        from .intent import classify
        from .sentiment import label, polarity
        for t in args.texts:
            r = classify(t)
            print(f"{t!r}\n  intent={r.label} signals={list(r.signals)} reason={r.reason}\n  sentiment={label(polarity(t))}")
    elif args.command == "schema":
        from sqlalchemy.dialects import postgresql
        from sqlalchemy.schema import CreateIndex, CreateTable

        from .db import metadata
        for table in metadata.sorted_tables:
            print(str(CreateTable(table).compile(dialect=postgresql.dialect())).strip() + ";\n")
            for idx in sorted(table.indexes, key=lambda i: i.name):
                print(str(CreateIndex(idx).compile(dialect=postgresql.dialect())).strip() + ";\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
