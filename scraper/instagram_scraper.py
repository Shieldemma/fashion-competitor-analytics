# scraper/instagram_scraper.py
# Run with:
# python scraper/instagram_scraper.py

from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import re

# ── Target brands ──────────────────────────────────────────────
COMPETITORS = {
    "veekeejames_official": 2000000,
    "ashluxe": 150000,
    "wflsncrm": 25000,
    "zivalagos": 80000,
    "yomicasual": 500000,
}

MAX_POSTS_PER_BRAND = 20
SLOW_MODE = True

posts = []

print("Starting Instagram scraper...")
print(f"Brands to scrape: {list(COMPETITORS.keys())}")
print("Chrome browser will open — do not close it.\n")

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False,
        slow_mo=1000
    )

    context = browser.new_context(
        viewport={"width": 1400, "height": 900}
    )

    page = context.new_page()

    for brand, followers in COMPETITORS.items():

        print(f"\n── Scraping @{brand} ──")

        profile_url = f"https://www.instagram.com/{brand}/"

        try:
            page.goto(profile_url, timeout=60000)
            time.sleep(8)

        except Exception as e:
            print(f"Could not open {brand}: {e}")
            continue

        # ── Collect post links ────────────────────────────────

        hrefs = []

        links = page.locator("a")

        total_links = links.count()

        for i in range(min(total_links, 150)):

            try:
                href = links.nth(i).get_attribute("href")

                if href and "/p/" in href:

                    full_url = "https://www.instagram.com" + href

                    if full_url not in hrefs:
                        hrefs.append(full_url)

            except:
                continue

        hrefs = hrefs[:MAX_POSTS_PER_BRAND]

        print(f"Found {len(hrefs)} post links")

        # ── Visit each post ───────────────────────────────────

        for idx, link in enumerate(hrefs):

            try:

                page.goto(link, timeout=60000)

                time.sleep(5)

                # ── Caption ───────────────────────────────

                caption = ""

                try:
                    caption_locator = page.locator("h1")

                    if caption_locator.count() > 0:
                        caption = caption_locator.first.inner_text()

                except:
                    pass

                # ── Likes ─────────────────────────────────

                likes = 0

                try:

                    page_text = page.locator("body").inner_text()

                    like_patterns = [
                        r"([\d,\.]+)\s+likes",
                        r"liked by",
                    ]

                    for pattern in like_patterns:

                        match = re.search(pattern, page_text, re.IGNORECASE)

                        if match and len(match.groups()) > 0:

                            raw_likes = match.group(1)

                            raw_likes = raw_likes.replace(",", "")

                            try:
                                likes = int(float(raw_likes))
                            except:
                                likes = 0

                            break

                except:
                    pass

                # ── Post Date ─────────────────────────────

                post_date = ""

                try:

                    time_locator = page.locator("time")

                    if time_locator.count() > 0:
                        post_date = time_locator.first.get_attribute("datetime")

                except:
                    pass

                # ── Save Row ──────────────────────────────

                posts.append({
                    "brand": brand,
                    "platform": "instagram",
                    "post_url": link,
                    "caption": caption,
                    "likes": likes,
                    "followers": followers,
                    "post_date": post_date
                })

                print(f"[{idx + 1}/{len(hrefs)}] Saved")

            except Exception as e:

                print(f"Error scraping post: {e}")

                continue

    browser.close()

# ── Save CSV ───────────────────────────────────────────────────

if posts:

    df = pd.DataFrame(posts)

    os.makedirs("data/raw", exist_ok=True)

    output_path = "data/raw/instagram_posts.csv"

    df.to_csv(output_path, index=False)

    print(f"\n✓ Saved {len(df)} posts")

    print(df.head())

else:

    print("\nNo posts scraped.")