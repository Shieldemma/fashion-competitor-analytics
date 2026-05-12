# Lagos Fashion Social Media Competitor Intelligence Report
**Client:** [Client Name]
**Analyst:** [Your Name]
**Date:** [Date]
**Period covered:** [Start Date] – [End Date]

---

## Executive Summary

This audit analysed [N] posts across 5 Lagos fashion competitors on Instagram over a [X]-week period. The primary finding is that **Instagram generates the highest purchase-intent behaviour** for Lagos fashion retail, driven by direct comment inquiries and DM-to-order culture. TikTok leads on raw reach but produces weaker buying signals.

**Bottom line recommendation:** Allocate 50% of social budget to Instagram, 30% to TikTok.

---

## Brands Audited

| Brand | Handle | Platform | Followers (approx) |
|-------|--------|----------|--------------------|
| Veekee James | @veekeejames_official | Instagram + TikTok | 2M |
| Ashluxe | @ashluxe | Instagram + TikTok | 150K |
| WAF Lagos | @wflsncrm | Instagram | 25K |
| Ziva Lagos | @zivalagos | Instagram + TikTok | 80K |
| Yomi Casual | @yomicasual | Instagram | 500K |

---

## Key Findings

### Finding 1 — Engagement Leader
**[Brand name]** achieved the highest average engagement rate at **[X]%**, outperforming the 5-brand average of **[Y]%** by **[N]x**.

Their content strategy — primarily [describe: e.g. "short behind-the-scenes Reels with clear product pricing in captions"] — drove significantly more comment activity than static product images.

### Finding 2 — Purchase Intent Leader
**[X]%** of posts on Instagram contained high-intent signals (price inquiries, delivery questions, DM order requests) compared to **[Y]%** on TikTok.

The Lagos fashion audience uses Instagram comments as a buying channel. Phrases like "price please," "do you deliver to Lekki," and "DM sent" appear frequently on high-performing posts.

### Finding 3 — Top Performing Content Types
| Content Type | Avg Engagement | Example |
|-------------|---------------|---------|
| Product Push | [X]% | "New collection drop — DM to order" |
| Storytelling | [X]% | "Behind the scenes at our Lagos studio" |
| Community | [X]% | "Thank you for 100K followers" |

### Finding 4 — Optimal Posting Time
Posts published between **7 PM and 10 PM WAT** generated the highest engagement, consistent across all brands audited.

---

## Platform Comparison

| Platform | Avg Engagement | High-Intent Rate | Best For |
|----------|---------------|-----------------|---------|
| Instagram | [X]% | [X]% | Purchase conversion |
| TikTok | [X]% | [X]% | Brand reach + awareness |
| Facebook | [X]% | [X]% | Older 35+ demographic |

---

## Budget Recommendation

Based on the data, the recommended monthly social media budget split is:

| Platform | Recommended Allocation | Rationale |
|----------|----------------------|-----------|
| Instagram | **50%** | Highest purchase-intent signals; Lagos fashion commerce lives here |
| TikTok | **30%** | Highest reach; growing social commerce adoption in Nigeria |
| Facebook | **15%** | Retargeting older demographic; lower organic performance |
| Twitter/X | **5%** | Minimal conversion signals; brand monitoring only |

---

## Methodology

- **Data collection:** Playwright browser automation (Python)
- **Posts analysed:** [N] posts across [X] brands
- **Engagement formula:** Likes ÷ Followers × 100
- **Intent classification:** Keyword-based NLP (Python) — 14 high-intent phrases, 12 medium-intent phrases
- **Sentiment analysis:** TextBlob polarity scoring
- **Database:** PostgreSQL (fashiondb)
- **Dashboard:** Streamlit web application

---

## Appendix

Full dataset available in: `data/processed/intent_classified.csv`
Charts available in: `reports/engagement_charts.png`
Interactive dashboard: run `streamlit run dashboard/streamlit_app.py`
