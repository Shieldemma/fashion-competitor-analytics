# Lagos Fashion Competitor Intelligence Platform

## Quick Start (follow these steps IN ORDER)

### Step 1 — Install Python dependencies
Open your terminal in VS Code and run:
```
pip install pandas numpy playwright sqlalchemy psycopg2-binary matplotlib scikit-learn streamlit textblob
playwright install chromium
```

### Step 2 — Set up PostgreSQL
1. Download and install PostgreSQL: https://www.postgresql.org/download/
2. Open pgAdmin (comes with PostgreSQL)
3. Create a new database called: fashiondb
4. Open the Query Tool in pgAdmin
5. Paste and run the contents of: database/schema.sql

### Step 3 — Run the scraper
```
python scraper/instagram_scraper.py
```
This saves raw data to: data/raw/instagram_posts.csv

### Step 4 — Clean the data
```
python analytics/clean_data.py
```
Saves to: data/cleaned/cleaned_posts.csv

### Step 5 — Load into database
```
python analytics/load_to_db.py
```

### Step 6 — Run engagement analytics
```
python analytics/engagement_analysis.py
```

### Step 7 — Run purchase intent classifier
```
python analytics/intent_classifier.py
```
Saves to: data/processed/intent_classified.csv

### Step 8 — Launch the dashboard
```
streamlit run dashboard/streamlit_app.py
```
Opens in your browser at: http://localhost:8501

---

## Project Structure
```
fashion_competitor_project/
├── data/
│   ├── raw/              ← scraped files land here
│   ├── cleaned/          ← after cleaning
│   └── processed/        ← after analytics
├── scraper/
│   └── instagram_scraper.py
├── analytics/
│   ├── clean_data.py
│   ├── load_to_db.py
│   ├── engagement_analysis.py
│   └── intent_classifier.py
├── database/
│   └── schema.sql
├── dashboard/
│   └── streamlit_app.py
└── reports/
    └── executive_report_template.md
```

## Target Brands
| Brand | Instagram Handle | Approx Followers |
|-------|-----------------|-----------------|
| Veekee James | @veekeejames_official | 2M |
| Ashluxe | @ashluxe | 150K |
| WAF Lagos | @wflsncrm | 25K |
| Ziva Lagos | @zivalagos | 80K |
| Yomi Casual | @yomicasual | 500K |

## Troubleshooting
- **Playwright not finding browser**: run `playwright install chromium` again
- **PostgreSQL connection error**: check your username/password in load_to_db.py and engagement_analysis.py
- **Instagram blocks scraper**: slow down the time.sleep() values (try 8-10 seconds)
- **TextBlob error**: run `python -m textblob.download_corpora`
