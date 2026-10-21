# analytics/engagement_analysis.py
# Runs the analytical SQL in sql/ against DATABASE_URL (default: local SQLite
# warehouse) and prints the results. Credentials come from .env, never from code.
# Run the pipeline first:  python -m fashion_intel run

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fashion_intel import db  # noqa: E402
from fashion_intel.config import SQL_DIR, get_settings  # noqa: E402

QUERIES = ["data_coverage", "top_brands", "intent_analysis", "platform_intent", "engagement_analysis", "posting_times"]


def main(include_all: bool = False) -> None:
    engine = db.get_engine(get_settings().database_url)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    for name in QUERIES:
        print(f"\n=== {name} ({'all collected posts' if include_all else 'audit window'}) ===")
        print(db.run_sql_file(engine, SQL_DIR / f"{name}.sql", {"include_all": int(include_all)}).to_string(index=False))


if __name__ == "__main__":
    main(include_all="--all" in sys.argv)
