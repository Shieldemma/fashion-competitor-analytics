# analytics/load_to_db.py - kept so the old command still works.
# Store stage (idempotent upsert into DATABASE_URL) now lives in the fashion_intel package; this runs the full,
# reproducible pipeline. Preferred command:  python -m fashion_intel run
# The original script is in git history (commit 548693e).

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fashion_intel.__main__ import main  # noqa: E402

if __name__ == "__main__":
    print("Note: analytics/load_to_db.py is a wrapper for 'python -m fashion_intel run'.\n")
    sys.exit(main(["run"]))
