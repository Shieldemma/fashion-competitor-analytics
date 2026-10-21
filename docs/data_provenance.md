# Data Provenance and Limitations

## Where the data came from

| Item | Value |
|---|---|
| Collection tool | Apify "Instagram Post Scraper" (run manually by the analyst) |
| Why not the in-repo Playwright scraper | Instagram rate-limits and login-walls unauthenticated browsing. The Playwright run was blocked after a few posts. |
| Input | 5 public profile URLs: `veekeejames_official`, `ashluxe`, `wflsncrm`, `zivalagos`, `yomicasual` |
| Scraper setting | about the latest 20 grid items per profile, plus up to ~10 latest comments per post |
| Raw file | `data/raw/apify_raw.csv`: 81 rows × 1,206 columns, gitignored (contains third-party usernames) |
| Collection date | Not recorded by the export. File modified 2026-05-13 UTC, and the newest comment is 2026-05-13 02:39 UTC, so the scrape ran **about 13 May 2026**. |
| Data type | **Real, public data.** No synthetic rows in the processed outputs. Run manifests record the file's SHA-256 hash. |

Every processed row carries `data_source`, `source_file`, `source_sha256`, `source_row` and `extracted_at_utc`.

## What the data covers, and what it doesn't

- **Platforms:** Instagram only. The brief's core question ("which platform drives the most purchase intent?") **cannot be answered** without data from a second platform.
- **Competitors:** 4 of 5. `yomicasual` returned "Empty or private data", so no posts were collected.
- **Time window:** the scraper took the latest 20 posts, not a date range. In the 60-day audit window (2026-03-13 → 2026-05-12), Ashluxe and Ziva Lagos have 20 posts each, Veekee James has 8, and WAF Lagos has **1**.
- **Comments:** about 10 latest comments per post, a **0.2%** sample of Veekee James' reported comments and 23–61% for the smaller brands. Comment-based rates describe *recent visible comments*, not all comments.
- **Collab posts:** 14 posts on competitors' grids are owned by partner accounts. They are attributed to the competitor and flagged `is_collab`. The sensitivity table shows results with them excluded.
- **Hidden likes:** 4 posts. These are stored as NULL and excluded from like statistics.
- **Follower counts:** not collected. `config/brands.json` holds the analyst's manual, rounded values with no as-of date. They are used only for a "reference" per-follower column, never for rankings. Yomi Casual's value is left unknown because the legacy code had two conflicting values.
- **Not observable at all:** DMs, WhatsApp conversations, website traffic, sales, ad spend. Purchase *signals* can be measured. Purchases cannot.

## Privacy

- Commenter handles are replaced by a salted one-way hash (`commenter_id`) in all derived outputs and in the database.
- `data/processed/comments.csv` and `data/raw/apify_raw.csv` are gitignored.
- ⚠️ `data/raw/real_comments.csv` (from the v1 pipeline) **contains raw commenter usernames and is tracked in git history.** Before making the repo public, consider removing it from tracking (`git rm --cached data/raw/real_comments.csv`). Rewriting history removes it from past commits, but that is a destructive operation, so do it deliberately.

## Replacing the inputs with your own authorised data

1. Collect public data you are authorised to use (Apify, an official API, or a client export).
2. Put the file in `data/raw/` with a new name. Never overwrite an existing raw file.
3. Edit `config/brands.json` if the competitors change. Record `follower_source` and `follower_as_of`, or leave `follower_count` as `null`.
4. Run `python -m fashion_intel run --input data/raw/<your_file>.csv`.
   - An Apify Instagram export is detected automatically.
   - Any other CSV needs at least `brand` and `post_url`. Optional: `platform`, `caption`, `likes`, `comments_count`, `views`, `post_date`, `data_source`. Column-name variants (`Likes`, `likesCount`, `timestamp`, …) are mapped automatically.
5. Check `data/processed/validation_report.csv` and the dashboard's **Data coverage** tab before reading any result.
6. For a true platform comparison, collect the **same competitors over the same date window** on each platform. A TikTok export can be converted into the generic posts CSV format with `platform=tiktok`.
