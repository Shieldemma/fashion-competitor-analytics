# Lagos Fashion Competitor Intelligence Platform

## Social Media Engagement & Purchase-Intent Audit

A complete end-to-end data analytics project that scrapes, cleans, analyses and visualises Instagram competitor data for 5 Lagos fashion brands to inform social media budget allocation.

## Brands Analysed
| Brand | Handle | Followers |
|-------|--------|-----------|
| Veekee James | @veekeejames_official | 2M |
| Ashluxe | @ashluxe | 150K |
| WAF Lagos | @wflsncrm | 25K |
| Ziva Lagos | @zivalagos | 77K |
| Yomi Casual | @yomicasual | 1M |

## Tech Stack
- **Scraping:** Apify Instagram Scraper
- **Processing:** Python, Pandas
- **Database:** PostgreSQL + SQLAlchemy
- **NLP:** TextBlob, keyword-based intent classifier
- **Dashboard:** Streamlit
- **Version Control:** Git + GitHub

## Key Findings
- Ziva Lagos has the highest purchase-intent signal rate (100% of high-intent posts)
- Veekee James dominates raw engagement (7.17% avg rate)
- Instagram drives stronger purchase-intent than other platforms
- Evening posts (7–10 PM WAT) generate highest engagement

## How to Run
```bash
conda activate fashion
python analytics/convert_apify.py
python analytics/clean_data.py
python analytics/intent_classifier.py
python analytics/load_to_db.py
streamlit run dashboard/streamlit_app.py
```

## Project Structure
├── scraper/          # Playwright + Apify scraper
├── analytics/        # ETL pipeline, NLP classifier, engagement analysis
├── database/         # PostgreSQL schema
├── dashboard/        # Streamlit interactive dashboard
├── sql/              # Analytical SQL queries
├── data/
│   ├── raw/          # Scraped data from Apify
│   ├── cleaned/      # After cleaning pipeline
│   └── processed/    # After NLP classification
└── reports/          # Executive report template
## Dashboard Preview
![Dashboard](docs/screenshots/dashboard.png)
