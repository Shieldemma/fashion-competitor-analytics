# LinkedIn post (attach `linkedin_carousel.pdf` as a document, or `linkedin_summary.png` as an image)

Generated visuals: `python scripts/build_linkedin_assets.py` (numbers come straight from the pipeline outputs).

---

Which social platform actually makes Lagos fashion customers buy? 🇳🇬👗

I took a real Upwork brief, "audit 5 Lagos fashion competitors across social platforms to decide the ad budget", and built it end to end as a portfolio project.

What I built:
🔹 Scraped public Instagram data (my own Playwright scraper got rate-limited, so I used Apify)
🔹 A Python ETL pipeline: validation, deduplication, provenance on every row, idempotent loads into SQL
🔹 An NLP purchase-intent classifier that handles negation and Nigerian Pidgin ("Wetin be the price?", "Una dey deliver to Abuja?")
🔹 An interactive Streamlit dashboard and 125 automated tests

What the data said:
📉 0 of 280 recent comments asked about price, ordering or delivery
💬 77% were emoji or compliments. Comments are for applause, not checkout
🏷️ One brand shows a ₦ price in 65% of its captions; the others show none

The part I'm proudest of: I did NOT recommend a budget split. Only Instagram data was collectable, so any "50% Instagram / 30% TikTok" answer would have been made up. My first version did exactly that, and auditing my own work was the most valuable lesson.

Instead I recommended a 6-week attribution test (a separate WhatsApp link, UTM tag and discount code per platform) to measure cost per order, not likes.

📊 Live dashboard: https://csxwsuvcgayckcnvkaw22s.streamlit.app
💻 Code + technical audit: github.com/Shieldemma/fashion-competitor-analytics

#DataAnalytics #Python #SQL #NLP #DataEngineering #Streamlit #Lagos #Nigeria #OpenToWork
