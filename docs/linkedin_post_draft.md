# LinkedIn post: draft (edit freely)

I rebuilt a portfolio project and changed its conclusion. 🧵

The brief (from a real Upwork job): audit 5 Lagos fashion brands across social media and find which platform drives the most purchase intent, so a retailer can split its ad budget.

What I built:
🔹 Scraped public Instagram data with Apify (Instagram rate-limited my own Playwright scraper)
🔹 A Python ETL pipeline with validation, provenance hashes, and idempotent loads into SQLite/PostgreSQL
🔹 A purchase-intent classifier for comments that handles negation, word boundaries, and Nigerian Pidgin ("Wetin be the price?", "Una dey deliver to Abuja?")
🔹 A Streamlit dashboard and 124 automated tests, including tests that check SQL and Python give the same numbers

What the data actually says:
📉 In a 60-day window, 0 of 280 public comments asked about price, ordering, or delivery. Almost half were emoji-only.
💬 Instagram comments on these accounts are for applause, not checkout. Buying likely happens in DMs and WhatsApp, which public scraping can't see.
🏷️ One brand puts the ₦ price in 65% of its captions. The others almost never do.

What I deliberately did NOT do: recommend a budget split. Only Instagram data was available, so any "Instagram 50% / TikTok 30%" answer would have been invented. My first version did exactly that, and auditing it was the most useful part of this project.

What I'd recommend instead: a 4–6 week attribution test with a separate WhatsApp link, UTM tag, and discount code per platform, measuring cost per conversation and cost per order.

Code, audit, and dashboard 👉 [GitHub link]

#DataAnalytics #Python #SQL #NLP #ETL #Streamlit #Lagos #FashionRetail #DataQuality
