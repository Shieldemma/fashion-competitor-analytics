# generate_sample_data.py
# Creates SYNTHETIC demo posts so the pipeline can be tried without scraping.
# Output: data/sample/synthetic_posts.csv. It NEVER writes to data/raw/.
# Every row is tagged data_source=synthetic_sample, and the dashboard shows a
# red "synthetic" banner. These numbers describe no real brand.
#
# Try the pipeline on it without touching the real warehouse:
#   python generate_sample_data.py
#   python -m fashion_intel run --input data/sample/synthetic_posts.csv --skip-db
# Then re-run `python -m fashion_intel run` to restore the real outputs.

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "sample" / "synthetic_posts.csv"

random.seed(42)
BRANDS = {"veekeejames_official": 40000, "ashluxe": 600, "wflsncrm": 500, "zivalagos": 60, "yomicasual": 800}
CAPTIONS = [
    "New collection just dropped! DM to order. Available in all sizes.",
    "Behind the scenes at our Lagos studio.",
    "Price: ₦85,000. Shop online, link in bio.",
    "Restock alert: the sold-out styles are back!",
    "Thank you for the love, family.",
    "Lagos Fashion Week ready. Swipe to see the full look.",
]


def main() -> None:
    now = datetime.now(timezone.utc)
    rows = []
    for brand, typical_likes in BRANDS.items():
        for i in range(random.randint(15, 22)):
            platform = random.choice(["instagram", "instagram", "tiktok"])
            published = now - timedelta(days=random.randint(1, 60), hours=random.randint(0, 23))
            rows.append({
                "brand": brand,
                "platform": platform,
                "post_url": f"https://www.{platform}.com/p/synthetic_{brand}_{i}/",
                "caption": random.choice(CAPTIONS),
                "likes": int(typical_likes * random.uniform(0.4, 2.5)),
                "comments_count": int(typical_likes * random.uniform(0.01, 0.05)),
                "post_date": published.isoformat(timespec="seconds"),
                "data_source": "synthetic_sample",
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Wrote {len(rows)} SYNTHETIC posts to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
