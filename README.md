# Lagos Fashion Competitor Intelligence

**An end-to-end, reproducible audit of purchase-intent signals across Lagos fashion brands on social media: scraping → validated ETL → NLP → SQL warehouse → Streamlit dashboard → evidence-based report.**

*Portfolio case study based on a public Upwork brief ("Data Analyst for Lagos Fashion Retail: Historical Scraping & Competitor Audit"). There was no client engagement, and the data is public Instagram content.*

**📊 Live dashboard:** _add your Streamlit Community Cloud link here_ · **🖼️ One-page summary:** [image](docs/linkedin/linkedin_summary.png) · **📑 Slides:** [carousel PDF](docs/linkedin/linkedin_carousel.pdf)

![Dashboard: executive summary](docs/screenshots/dashboard_v2_hero.png)

## The question and the honest answer

> *Which social platform drives the most purchase-intent behaviour for 5 Lagos fashion competitors, to inform a budget split?*

| What I found | Evidence |
|---|---|
| **The platform question can't be answered from this data.** Instagram blocked direct scraping, and Apify returned Instagram only. | 80 posts · 553 audience comments · 1 platform |
| **Public Instagram comments carry almost no purchase intent.** In the 60-day window, **0 of 280** comments ask about price, ordering, delivery or availability (95% CI 0–1.35%). | 46% emoji-only, 30% compliments |
| Across all collected posts, 8 of 553 comments (1.45%) show shopping signals, all on older Veekee James posts. | sensitivity table |
| Brands behave differently: **Ziva Lagos shows a ₦ price in 65% of captions**. The others almost never do. | caption analysis |
| **Recommendation:** don't set a budget split from engagement. Run a 4–6 week attribution test (per-platform WhatsApp links, UTM, discount codes) and measure cost per conversation and per order. | [executive summary](reports/executive_summary.md) |

A big part of this project is **knowing what the data can't support**. The v1 version of this repo claimed an "Instagram > TikTok" result and a 55/30/10/5 budget split that no collected data backed up. The [technical audit](reports/technical_audit.md) documents that and every fix.

## What's inside

| Skill | Where |
|---|---|
| Web scraping (Playwright attempt + Apify) | `scraper/`, [provenance](docs/data_provenance.md) |
| ETL: validation, quarantine, idempotent loads, provenance hashes | `fashion_intel/extract.py`, `validate.py`, `transform.py`, `db.py` |
| Data quality: `1.2K`/`2.3M` parsing, hidden likes = NULL not 0, UTC→WAT, collab attribution, dedupe | `fashion_intel/clean.py` |
| NLP: 5-class purchase-intent rules (negation, Pidgin, word boundaries), separate sentiment, evaluation | `fashion_intel/intent.py`, [taxonomy](docs/intent_taxonomy.md), [evaluation](reports/classifier_evaluation.md), [model decision](docs/nlp_model_decision.md) |
| SQL: portable SQLite/PostgreSQL queries, tested against Python | `sql/`, `database/schema.sql` |
| Statistics: denominators, Wilson intervals, sensitivity analysis | `fashion_intel/metrics.py`, [definitions](docs/data_dictionary.md) |
| BI dashboard: executive one-pager, 10 interactive Altair chart types, filters, KPIs | `dashboard/streamlit_app.py`, `dashboard/charts.py` |
| Testing: 125 pytest tests incl. SQL-vs-Python and dashboard smoke tests | `tests/` |

Architecture diagram: [docs/architecture.md](docs/architecture.md).

## The dashboard

The **Executive summary** tab answers the client's brief on one page:

1. **Brief scorecard:** what was asked (5 brands, several platforms, 2 months) vs. what the data covers
2. **Purchase-intent funnel:** comments → words → any shopping cue → explicit buy request → people → sales (not observable)
3. **What audiences actually write:** praise, emoji, questions, per brand
4. **Recent vs. older posts:** where the few buying questions are, with 95% confidence intervals
5. **Coverage timeline:** every collected post against the 60-day audit window
6. **Competitor scorecard + caption behaviour,** then **the answer and a costed next step**

Other tabs: purchase-intent detail and comment explorer, engagement (per-post spread, format, weekly volume),
posting time (heatmap and weekday performance), data coverage and quality checks, method, and raw data with CSV download.
All charts respond to the sidebar filters (brand, platform, date, audit window, collab and pinned posts).

| Executive summary (full page) | Purchase intent | Engagement |
|---|---|---|
| ![](docs/screenshots/dashboard_v2_overview.png) | ![](docs/screenshots/dashboard_v2_intent.png) | ![](docs/screenshots/dashboard_v2_engagement.png) |
| **Posting time** | **Data coverage** | |
| ![](docs/screenshots/dashboard_v2_timing.png) | ![](docs/screenshots/dashboard_v2_coverage.png) | |

## Quick start (macOS)

```bash
# 1. Python 3.11+ (developed on 3.13). From the project folder:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Put the Apify export at data/raw/apify_raw.csv (not committed: it contains third-party usernames)

# 3. Run the whole pipeline (creates a local SQLite warehouse, so no database server is needed)
python -m fashion_intel run

# 4. Open the dashboard
streamlit run dashboard/streamlit_app.py

# 5. Tests and classifier evaluation
python -m pytest -q
python -m fashion_intel evaluate
```

### Commands

| Command | What it does | Writes |
|---|---|---|
| `python -m fashion_intel run` | Extract → Validate → Clean → Enrich → Classify → Store → Analyze → Report | `data/processed/`, warehouse, `reports/findings_generated.md`, `logs/pipeline.log` |
| `python -m fashion_intel run --skip-db` | Same, without the database | no database |
| `python -m fashion_intel run --input FILE --window-end 2026-05-12 --window-days 60` | Custom input or window | |
| `python -m fashion_intel classify "How much is this?"` | Try the classifier | nothing |
| `python -m fashion_intel evaluate` | Precision/recall/F1 on labelled sets | `reports/classifier_evaluation.md` |
| `python -m fashion_intel schema` | Print PostgreSQL DDL | stdout |
| `python analytics/engagement_analysis.py [--all]` | Run every `sql/*.sql` query against the warehouse | nothing |
| `python generate_sample_data.py` | **Synthetic** demo data | `data/sample/` only |

The raw file is only ever read. Re-running the pipeline is safe: loads are upserts in one transaction, so a rerun gives the same database state.

### Deploy the dashboard online (free, Streamlit Community Cloud)

The dashboard reads only the committed files in `data/processed/`, so it runs online without the raw data or a database.
1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and click **Create app**.
3. Repository `Shieldemma/fashion-competitor-analytics`, branch `main`, main file `dashboard/streamlit_app.py`. Under *Advanced settings*, pick Python 3.12.
4. Deploy, then paste the `*.streamlit.app` link at the top of this README.

### Using PostgreSQL instead of SQLite

```bash
cp .env.example .env
# edit .env:  DATABASE_URL=postgresql+psycopg2://YOUR_USER:YOUR_PASSWORD@localhost:5432/fashion_intel
createdb fashion_intel          # Postgres.app: use its bundled createdb/psql
python -m fashion_intel run
```

The pipeline creates its own tables (`competitor_brands`, `social_posts`, `audience_comments`, `pipeline_runs`). It never drops or alters existing tables, including the v1 `brands`/`posts` tables.

## Data, provenance and limitations

- **Real public data** from Apify, scraped on about 13 May 2026: 4 of 5 competitors (Yomi Casual returned nothing), Instagram only, latest ~20 posts per brand, ~10 comments per post.
- Commenter handles are **pseudonymised**. Follower counts are manual reference values and are never used for ranking.
- Full details, and how to swap in your own authorised data: [docs/data_provenance.md](docs/data_provenance.md).

## Project structure

```
fashion_intel/        pipeline package (config, extract, validate, clean, transform, intent, sentiment, db, metrics, report, evaluate)
config/brands.json    competitor registry (+ follower source/as-of)
dashboard/            Streamlit app
sql/                  analytical queries (SQLite + PostgreSQL)
database/             schema.sql (generated PostgreSQL DDL)
data/raw/             raw inputs (read-only)
data/processed/       tidy tables, analysis/*.csv, validation report, run manifest
data/evaluation/      labelled comments + synthetic challenge set
reports/              executive summary, generated findings, classifier evaluation, technical audit
docs/                 architecture, data dictionary, intent taxonomy, NLP decision, provenance
analytics/            engagement_analysis.py: runs every sql/*.sql query against the warehouse
scraper/              experimental Playwright scraper
scripts/              build_linkedin_assets.py: LinkedIn carousel + summary image from the data
tests/                pytest suite
```

## Author

Otuekong Emmanuel · [GitHub @Shieldemma](https://github.com/Shieldemma)
