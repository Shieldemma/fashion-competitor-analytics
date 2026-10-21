# analytics/convert_apify.py - kept so the old command still works.
# Extract stage (Apify export -> tidy posts + comments) now lives in the fashion_intel package; this runs the full,
# reproducible pipeline. Preferred command:  python -m fashion_intel run
# The original script is in git history (commit 548693e).

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fashion_intel.__main__ import main  # noqa: E402

if __name__ == "__main__":
    print("Note: analytics/convert_apify.py is a wrapper for 'python -m fashion_intel run'.\n")
    sys.exit(main(["run", "--skip-db"]))
