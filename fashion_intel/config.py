"""Paths and settings.

All paths are resolved from the project root (the folder containing this
package), so scripts work no matter which directory you run them from.
Settings come from environment variables, optionally loaded from a local
`.env` file. Values are never printed; use `describe_database_url` for logs.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
EVAL_DIR = DATA_DIR / "evaluation"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOG_DIR = PROJECT_ROOT / "logs"
SQL_DIR = PROJECT_ROOT / "sql"
BRANDS_CONFIG = PROJECT_ROOT / "config" / "brands.json"

DEFAULT_RAW_INPUT = RAW_DIR / "apify_raw.csv"
DEFAULT_DATABASE_URL = f"sqlite:///{WAREHOUSE_DIR / 'fashion_intel.db'}"

# Lagos is UTC+1 all year (no daylight saving).
LOCAL_TZ = "Africa/Lagos"

log = logging.getLogger("fashion_intel")


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (KEY=VALUE lines). Existing env vars win."""
    path = path or PROJECT_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    database_url: str
    raw_input: Path
    audit_window_days: int
    audit_window_end: str | None  # ISO date; None = newest post in the data


def get_settings() -> Settings:
    load_dotenv()
    brands = load_brand_config()
    return Settings(
        database_url=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        raw_input=Path(os.environ.get("RAW_INPUT_PATH") or DEFAULT_RAW_INPUT),
        audit_window_days=int(os.environ.get("AUDIT_WINDOW_DAYS") or brands.get("audit_window_days", 60)),
        audit_window_end=os.environ.get("AUDIT_WINDOW_END") or None,
    )


def describe_database_url(url: str) -> str:
    """Safe-to-log description: dialect and database name, no credentials."""
    from sqlalchemy.engine import make_url

    u = make_url(url)
    if u.get_backend_name() == "sqlite":
        return f"sqlite ({Path(u.database).name if u.database else 'memory'})"
    return f"{u.get_backend_name()} database '{u.database}' on {u.host or 'localhost'}"


def load_brand_config(path: Path = BRANDS_CONFIG) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def setup_logging(name: str = "pipeline") -> Path:
    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"{name}.log"
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")
    root = logging.getLogger("fashion_intel")
    root.setLevel(logging.INFO)
    if not root.handlers:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    return log_path
