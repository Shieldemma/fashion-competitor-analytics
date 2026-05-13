# Lagos Fashion Social Media Competitor Intelligence
## Executive Summary Report

**Prepared by:** Otuekong Emmanuel (Shieldemma)
**Date:** May 2026
**Scope:** 66 posts, 569 comments, 4 brands, 2-month audit

---

## Objective
Determine which social media platform and content strategy drives the strongest purchase-intent behaviour among Lagos fashion consumers, to inform budget allocation decisions.

---

## Brands Audited
| Brand | Handle | Followers | Category |
|-------|--------|-----------|----------|
| Veekee James | @veekeejames_official | 2M | Bridal/Luxury |
| Ashluxe | @ashluxe | 150K | Streetwear |
| WAF Lagos | @wflsncrm | 25K | Culture/Streetwear |
| Ziva Lagos | @zivalagos | 77K | Women's RTW |

---

## Key Findings

### Finding 1 — Purchase Intent Leader: Ziva Lagos
Ziva Lagos generated 100% of all High Intent posts in the audit. Their captions consistently include direct purchase signals: product names, Naira prices (₦50,500–₦110,000), restock alerts, and direct calls to action ("Shop online at www.zivalagos.com").

### Finding 2 — Engagement Leader: Veekee James
Veekee James achieved 7.17% average engagement rate — significantly above the 4-brand average of 2.26%. However this is skewed by viral outlier posts (535K likes). Median engagement is more representative.

### Finding 3 — Content Strategy Differences
| Brand | Content Style | Purchase Intent |
|-------|--------------|-----------------|
| Ziva Lagos | Product-first, price-visible | High |
| Veekee James | Bridal storytelling | Medium |
| WAF Lagos | Community/culture | Low |
| Ashluxe | Aesthetic/editorial | Low |

### Finding 4 — Optimal Posting Time
Posts published between 12 PM and 6 PM WAT generated the highest engagement across all brands.

---

## Budget Recommendation
| Platform | Recommended Allocation | Rationale |
|----------|----------------------|-----------|
| Instagram | 55% | Highest purchase intent, strongest Lagos fashion commerce |
| TikTok | 30% | Highest reach potential, growing commerce behaviour |
| Facebook | 10% | Older demographic, lower conversion |
| Twitter/X | 5% | Minimal fashion conversion signals |

---

## Methodology
- Data collected via Apify Instagram Scraper
- 66 posts and 569 comments extracted
- Engagement rate = likes / followers × 100
- Purchase intent classified via keyword NLP (14 high-intent phrases)
- Sentiment analysis via TextBlob
- Data stored in PostgreSQL, visualised in Streamlit

---

## Limitations
- Instagram hides like counts on some posts (returned null)
- Yomi Casual data unavailable due to scraping restrictions
- Sample size of 66 posts — larger dataset would improve confidence
- Historical 2-month window only

---

## Recommendation
A Lagos fashion retailer should prioritise Instagram as their primary commerce platform, adopt Ziva Lagos-style product-first captions with visible pricing, and post between 12–6 PM WAT for maximum engagement.
