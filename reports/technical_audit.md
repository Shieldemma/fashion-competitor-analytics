# Technical Audit — Lagos Fashion Competitor Intelligence

**Audit date:** 2026-10-21
**Scope:** every file in the repository, plus read-only profiling of all CSVs
**Baseline commit:** `62431a5` (with uncommitted working-tree changes snapshotted as `548693e` on branch `pipeline-v2`)

This document records the state of the project *before* the pipeline refactor. Everything in it was checked against the code and data, not taken from the README.

---

## 1. Architecture as found

```
Apify Instagram Post Scraper (run manually, exported to CSV)
        │  data/raw/apify_raw.csv   (81 rows × 1,206 columns, gitignored)
        ▼
analytics/convert_apify.py ──► data/raw/instagram_posts.csv   (overwritten every run)
                           └─► data/raw/real_comments.csv     (overwritten every run)
        ▼
analytics/clean_data.py    ──► data/cleaned/cleaned_posts.csv (also classifies intent)
        ▼
analytics/intent_classifier.py ──► data/processed/intent_classified.csv (classifies intent again)
        ▼
analytics/load_to_db.py    ──► PostgreSQL `fashiondb` (DELETE FROM posts, then insert)
        ▼
analytics/engagement_analysis.py (reads Postgres, different credentials) ──► charts, CSVs
dashboard/streamlit_app.py (reads the CSV, not the database)
```

| Component | What it does | Status |
|---|---|---|
| `scraper/instagram_scraper.py` | Playwright browser scraper | **Not used for the current data.** Runs on import (no `main`), overwrites `data/raw/instagram_posts.csv`, records `likes=0` when it fails to parse. |
| Apify export | The real data source | Works. 4 of 5 brands returned posts. |
| `analytics/convert_apify.py` | Flattens the Apify export into posts and comments | Works, but see problems D1–D5. |
| `analytics/clean_data.py` | Dedupes, parses likes, computes engagement, classifies intent | Works, but contains its own copy of the intent rules. |
| `analytics/intent_classifier.py` | Keyword intent + TextBlob sentiment | Works mechanically. Classifies **brand captions**, not audience comments. |
| `analytics/load_to_db.py` | Loads into PostgreSQL | **Fails on the current data** (foreign-key violation, see S2). Not idempotent. |
| `analytics/engagement_analysis.py` | Business questions | Hard-coded password `"password"` and user `postgres`, which differ from `load_to_db.py`. Calls `plt.show()`, which blocks. |
| `database/schema.sql` | Two tables + seed | Partial: no indexes, no comments table, seeds disagree with the code. |
| `sql/*.sql` | Analytical queries | **3 of 4 files are empty** (`engagement_analysis.sql`, `intent_analysis.sql`, `posting_times.sql`). |
| `dashboard/streamlit_app.py` | Streamlit dashboard | Runs, but shows wrong headline numbers (see V1–V4). |
| `generate_sample_data.py` | Synthetic data generator | **Overwrites the real raw file** `data/raw/instagram_posts.csv`. Invents TikTok posts. |
| `tests/`, `notebooks/` | — | **Empty.** |
| `.env` | — | Empty (0 bytes). No `.env.example`. |

---

## 2. Is the data real, sample, or mixed?

**Real, with a synthetic generator alongside.**

- `data/raw/apify_raw.csv` is a genuine Apify Instagram export. It has Instagram shortcodes, owner IDs, CDN URLs, and an Apify `error` row (`no_items: Empty or private data for provided input` for `yomicasual`).
- The CSVs in the repo were derived from that export. They contain no `sample_` URLs, so the synthetic generator was not the source of the current files.
- `generate_sample_data.py` writes fake data, including a fake TikTok platform, **to the same path** as the real converted file. Running it once would silently replace real data with synthetic data. The dashboard cannot tell the two apart.
- **Collection timestamp:** the export does not record when the scrape ran. The newest comment timestamp is `2026-05-13 02:39 UTC`, and the file was last modified on 2026-05-13, so the scrape happened on about **13 May 2026**.

---

## 3. Coverage against the brief

The brief asks for **5 competitors × multiple platforms × a 2-month historical window**.

| Requirement | Found | Verdict |
|---|---|---|
| 5 competitors | 4 with data. `yomicasual` returned **0 posts** (Apify: empty or private). | ❌ 4/5 |
| Multiple platforms | **Instagram only.** Every row is Instagram. No TikTok, Facebook or X data exists. | ❌ The platform question cannot be answered with this data. |
| 2-month window | The scraper took the **latest 20 grid items per profile**, not a date window. The 60-day window ending at the newest post (2026-03-13 → 2026-05-12) covers only part of the data (table below). | ⚠️ Partial |

Rows per profile:

| Profile scraped | Rows | In 60-day window | Collab posts (other owner) | Hidden like counts | Date span |
|---|---|---|---|---|---|
| ashluxe | 20 | 20 | 0 | 0 | 2026-03-17 → 2026-04-29 |
| zivalagos | 20 | 20 | 2 | 0 | 2026-04-16 → 2026-05-12 |
| veekeejames_official | 20 | 8 | 5 | 3 | **2024-01-14** → 2026-05-10 (3 pinned posts) |
| wflsncrm | 20 | **1** | 7 | 1 | **2025-08-23** → 2026-04-03 |
| yomicasual | 0 (1 error row) | 0 | – | – | – |

Comments: the export contains **at most 10 "latest comments" per post** (550 top-level comment texts, plus replies), while the real comment totals run into the thousands (one post has 13,703 comments). Comment-based metrics are therefore based on a **sample of recent comments**, not every comment.

---

## 4. Problems found

### Data and ETL

- **D1. Collab posts mislabelled as separate brands.** `convert_apify.py` takes `brand` from `ownerUsername`. Instagram collab posts that appear on a competitor's grid are owned by another account (e.g. `officialosas`, `adeola.fadola`, `veekee_james`), so they turn up as **10 extra "brands"**. The working-tree CSVs have 14 brand values. The committed version silently dropped these 15 posts (66 rows). The correct attribution is the profile that was scraped (`inputUrl`), with an `is_collab` flag.
- **D2. Invented follower counts.** Any brand missing from the dictionary gets `followers = 100000` (`convert_apify.py`) or `10000` (`clean_data.py`). That produced an engagement rate of **256.7%** for `veekee_james`. The followers dictionary itself disagrees between files (`zivalagos` 77K vs 80K, `yomicasual` 1M vs 500K). It has no source and no as-of date, and the export contains no follower data.
- **D3. Hidden like counts treated as real numbers.** Instagram returns `likesCount = -1` when likes are hidden (4 posts). These become `likes = -1`, which gives negative engagement rates and lowers the averages. They should be stored as unknown (NULL).
- **D4. Time zone error.** `post_hour` is taken from the UTC timestamp, but the report talks about "WAT". Lagos is UTC+1, so every hour-of-day finding is off by one hour.
- **D5. Every stage overwrites its output, including files under `data/raw/`.** There is no provenance (source file, hash, run ID), no validation of required columns, and no run log.
- **D6. Fragile paths.** Every script assumes the working directory is the project root.
- **D7. The 1.2K/2.3M parser is too loose.** `clean_likes` checks whether `"m"` or `"k"` appears *anywhere* in the string, and returns 0 when parsing fails, which turns unknown values into real zeros.
- **D8. Privacy.** `data/raw/real_comments.csv` (committed to git) stores commenter usernames of private individuals. For a public portfolio, these should be pseudonymised in derived outputs.
- **D9. `.gitignore`** lists `data/cleaned/` and `data/processed/`, but both are already tracked. It also has the Miniconda line repeated six times.

### Purchase-intent classification

- **N1. Wrong unit of analysis.** The classifier runs on **brand captions**. A caption saying "DM to order" measures the *seller's* call to action, not *customer* purchase intent. Audience purchase intent lives in the **comments**, which are extracted but never classified.
- **N2. Duplicate, diverging rules.** `clean_data.py` and `intent_classifier.py` hold different keyword lists. `clean_data.py` has no "No Signal" class, so "Low Intent" (54) and "No Signal" (40) mean different things in the two files.
- **N3. Substring matching with no word boundaries.** Measured on the legacy rules:

| Input | Legacy label | Problem |
|---|---|---|
| "Nice costume" | High | `cost` ⊂ `costume` |
| "Our admin team is random" | Medium | `dm` ⊂ `admin`, `random` |
| "I don't want to buy this." | Medium | No negation handling |
| "The delivery was terrible." | Medium | A complaint counted as shopping intent |
| "I want to order this outfit." | Medium | An explicit order request is under-rated |
| "I wan buy am" (Pidgin) | Medium | No Pidgin patterns |

- **N4. Compliments counted as intent.** `love`, `fire` and `wow` are "Low Intent", and "want" matches as a substring.
- **N5. No evaluation.** No labelled data, no precision or recall, and no tests. Labels were reported as findings without validation.
- **N6. Sentiment is mixed in.** TextBlob ignores emojis, so the most common comment form ("😍🔥") scores neutral. Sentiment is computed on captions, not on audience comments.

### Database and SQL

- **S1. Not idempotent.** `load_to_db.py` runs `DELETE FROM posts` and then a plain insert. A failed insert leaves the table empty, because the delete is committed in a separate transaction.
- **S2. Load fails on the current data.** `posts.brand_handle REFERENCES brands(handle)` rejects the 10 collab owners from D1.
- **S3.** Credentials are hard-coded in two different forms. There is no `DATABASE_URL`, and no comments table, indexes, run table or provenance columns.
- **S4.** SQL averages include `-1` likes and the invented follower counts. Three SQL files are empty.
- **S5.** The current local PostgreSQL requires a password the code does not supply, so `load_to_db.py` cannot connect as written. *(Not changed. Credentials belong in `.env`.)*

### Dashboard

- **V1. "Top brand" KPI shows `veekee_james`**, a collab account with an invented follower count (256.7% engagement). It also ignores the brand filter.
- **V2. The budget recommendation table (50/30/15/5 across Instagram/TikTok/Facebook/X) is hard-coded.** No TikTok, Facebook or X data exists, so it is not supported by any data in the project.
- **V3.** "Avg engagement rate" is a mean across mixed follower bases and includes the negative and inflated values from D2 and D3.
- **V4.** The footer says the data was "collected via Playwright scraper", but it came from Apify. There are no date or platform filters, no definitions, and no data-coverage section.

### Reporting

- **R1. `reports/executive_summary.md` makes claims the data does not support:** "Instagram drives stronger purchase-intent than other platforms" (no other platform was collected), a 55/30/10/5 budget split, "2-month audit" (only 2 of 4 brands are mostly inside the window), and "Ziva generated 100% of High Intent posts" (that is caption copywriting style, not customer intent).
- **R2.** The README's "Evening posts (7–10 PM WAT)" finding contradicts the executive summary's "12–6 PM". The README also references a missing `docs/screenshots/dashboard.png` and says Yomi Casual was analysed.
- **R3.** The report template comes pre-filled with conclusions ("Instagram generates the highest purchase-intent…").

### Reproducibility

- **P1.** `requirements.txt` pins 60 packages, including playwright, uvicorn and starlette, which the core pipeline does not need. pytest is missing. README uses `conda activate fashion`, but the project ships a `venv/`.
- **P2.** No tests and no validation procedure.

---

## 5. What works and is worth keeping

- The Apify export is real, reasonably rich data (likes, comments, video views, comment samples, collab metadata).
- PostgreSQL + SQLAlchemy is a sensible store. The schema idea (brands → posts) is right.
- Streamlit is a good dashboard choice for a portfolio.
- The Playwright scraper documents why Apify was needed: Instagram rate-limits unauthenticated browsing.

---

## 6. Recommended changes (implemented on branch `pipeline-v2`)

1. **One package, `fashion_intel/`**, with explicit stages: Extract → Validate → Clean → Enrich → Classify → Store → Analyze → Report. One CLI: `python -m fashion_intel run`.
2. **Attribute posts to the scraped profile** (`inputUrl`), keep `owner_username`, and flag `is_collab` and `is_pinned`.
3. **Unknown means NULL**: hidden likes, missing views, and unknown followers. Follower counts move to `config/brands.json` with an explicit `source` and `as_of`. The engagement rate is labelled "reference only".
4. **Classify audience comments** with a tested, word-boundary-aware rule engine (negation, Pidgin, affordability). Keep caption call-to-action detection as a separate "seller signal". Keep sentiment separate.
5. **Evaluation set** with documented labels and precision, recall and F1 reported, with an honest caveat about sample size and who labelled it.
6. **Idempotent upserts** keyed on stable IDs, a `pipeline_runs` table, and portable SQL that is tested against the Python metrics. `DATABASE_URL` comes from `.env`. Defaults to a local SQLite file so the project runs with zero setup, and PostgreSQL is supported via `.env`.
7. **Raw data is never overwritten.** The synthetic generator writes to `data/sample/` and is labelled synthetic.
8. **Dashboard rebuilt on the same metrics module**, with a provenance banner and no unsupported budget split.
9. **Reports regenerated from verified outputs.** The old executive summary is archived, not deleted.

---

## 7. Status after the refactor (2026-10-21)

| Problem | Status | Where |
|---|---|---|
| D1 collab posts as fake brands | Fixed: attributed to scraped profile, `is_collab` flag, sensitivity scenario | `extract.py`, `metrics.SCENARIOS` |
| D2 invented followers | Fixed: no fallbacks, manual values documented as reference-only, Yomi left unknown | `config/brands.json` |
| D3 hidden likes = -1 | Fixed: NULL + `likes_hidden` | `clean.parse_count` |
| D4 UTC labelled as WAT | Fixed: `Africa/Lagos` conversion, tested | `clean.add_local_time_parts` |
| D5–D7 overwrites, no provenance/validation, fragile paths, loose parser | Fixed | `extract.py`, `validate.py`, `config.py` |
| D8 commenter usernames | Fixed in all new outputs (pseudonymised). **Open:** `data/raw/real_comments.csv` remains in git history, so removing it is your decision | `docs/data_provenance.md` |
| N1–N6 classifier | Fixed: one classifier on audience comments, 5 documented labels, evaluated | `intent.py`, `reports/classifier_evaluation.md` |
| S1–S4 database | Fixed: upserts, single transaction, FK enforced, run log, portable tested SQL | `db.py`, `sql/` |
| S5 Postgres auth | Unchanged by design: credentials go in `.env` (`DATABASE_URL`). The default is SQLite | `.env.example` |
| V1–V4 dashboard | Fixed: rebuilt on `metrics.py`, provenance banner, no hard-coded budget split | `dashboard/streamlit_app.py` |
| R1–R3 reports | Fixed: v1 summary archived with warning, new summary from verified numbers, neutral template | `reports/` |
| P1–P2 dependencies/tests | Fixed: 8 core pins + optional scraper file, 124 tests | `requirements*.txt`, `tests/` |
