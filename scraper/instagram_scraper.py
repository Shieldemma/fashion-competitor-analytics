# scraper/instagram_scraper.py
# Experimental Playwright scraper for public Instagram profiles.
#
# Why the project's data came from Apify instead: Instagram rate-limits and
# login-walls unauthenticated browsing, so this script typically collects only
# a handful of posts before it is blocked. It is kept to document the attempt
# and as a starting point. Respect Instagram's Terms of Use and robots rules,
# and collect only public data you are authorised to use.
#
# Run (opens a visible Chrome window):
#   pip install -r requirements-scraper.txt && playwright install chromium
#   python scraper/instagram_scraper.py
# Output: data/raw/playwright_posts_<UTC timestamp>.csv. A new file each run;
# it never overwrites existing raw data. Feed it to the pipeline with:
#   python -m fashion_intel run --input data/raw/playwright_posts_<...>.csv

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MAX_POSTS_PER_BRAND = 20
LIKES_RE = re.compile(r"([\d,.]+\s*[KkMm]?)\s+likes", re.IGNORECASE)


def competitors() -> list[str]:
    cfg = json.loads((ROOT / "config" / "brands.json").read_text(encoding="utf-8"))
    return [b["brand_handle"] for b in cfg["brands"] if b["platform"] == "instagram"]


def scrape() -> pd.DataFrame:
    from playwright.sync_api import sync_playwright

    posts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
        for brand in competitors():
            print(f"\n── Scraping @{brand} ──")
            try:
                page.goto(f"https://www.instagram.com/{brand}/", timeout=60000)
                time.sleep(8)
            except Exception as exc:
                print(f"Could not open {brand}: {exc}")
                continue

            hrefs = []
            links = page.locator("a")
            for i in range(min(links.count(), 150)):
                try:
                    href = links.nth(i).get_attribute("href")
                except Exception:
                    continue
                if href and ("/p/" in href or "/reel/" in href):
                    url = "https://www.instagram.com" + href if href.startswith("/") else href
                    if url not in hrefs:
                        hrefs.append(url)
            hrefs = hrefs[:MAX_POSTS_PER_BRAND]
            print(f"Found {len(hrefs)} post links")

            for idx, link in enumerate(hrefs):
                try:
                    page.goto(link, timeout=60000)
                    time.sleep(5)
                    caption = page.locator("h1").first.inner_text() if page.locator("h1").count() else ""
                    match = LIKES_RE.search(page.locator("body").inner_text())
                    likes = match.group(1) if match else None      # unknown stays unknown, never 0
                    post_date = page.locator("time").first.get_attribute("datetime") if page.locator("time").count() else None
                    posts.append({
                        "brand": brand, "platform": "instagram", "post_url": link, "caption": caption,
                        "likes": likes, "post_date": post_date,
                        "collected_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "data_source": "playwright_instagram",
                    })
                    print(f"[{idx + 1}/{len(hrefs)}] saved")
                except Exception as exc:
                    print(f"Error scraping post: {exc}")
        browser.close()
    return pd.DataFrame(posts)


def main() -> None:
    df = scrape()
    if df.empty:
        print("\nNo posts scraped.")
        return
    out = ROOT / "data" / "raw" / f"playwright_posts_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\n✓ Saved {len(df)} posts to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
