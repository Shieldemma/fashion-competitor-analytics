# Lagos Fashion Competitor Audit: Executive Summary

**Prepared by:** Otuekong Emmanuel · **Portfolio case study** inspired by a public Upwork brief (no client engagement)
**Data:** public Instagram posts and comments, collected with Apify on about 13 May 2026
**Audit window:** 13 Mar → 12 May 2026 (60 days) · **Pipeline run:** `20261021T140435Z-611425`
**Every number below comes from `reports/findings_generated.md` for that run.**

---

## The brief

> "Conduct a 2-month historical audit of 5 Lagos-based fashion retail competitors across social media platforms … identify which platform drives the most purchase-intent behaviour to inform a social media budget allocation decision."

## Bottom line

1. **The platform question cannot be answered with this data, and the honest move is to say so.** Only Instagram was collected, so no platform comparison or budget split is supported.
2. **On Instagram, public comments carry almost no purchase intent.** In the audit window, **0 of 280** sampled audience comments contain a shopping signal (95% CI 0–1.35%). 46% are emoji-only and 30% are compliments.
3. Across **all** collected posts, including older and pinned ones, **8 of 553** comments (1.45%) are shopping signals. All 8 are on **Veekee James** posts published *before* the window, mostly pinned or bridal posts that keep attracting comments.
4. **What the brands do differs sharply:** **Ziva Lagos** puts a ₦ price in **65%** of captions and a call to action in **75%**. The other three brands almost never do.

## Coverage (read this before the findings)

| Competitor | Posts collected | Posts in window | Sampled audience comments (in window) | Note |
|---|---|---|---|---|
| Veekee James | 20 | 8 | 78 | 5 collab posts, 3 with hidden likes, 3 pinned (2024) |
| Ashluxe | 20 | 20 | 117 | |
| WAF Lagos | 20 | **1** | 10 | Posts rarely, so 20 posts span Aug 2025–Apr 2026 |
| Ziva Lagos | 20 | 20 | 75 | |
| Yomi Casual | **0** | 0 | 0 | Apify: "empty or private data" |

The scraper returns only about 10 recent comments per post. For Veekee James that is **0.2%** of all reported comments.

## Findings

### 1. Purchase intent in public comments is close to zero

| Scope | Sampled comments | High | Medium | High + medium rate (95% CI) |
|---|---|---|---|---|
| Audit window (primary) | 280 | 0 | 0 | 0.0% (0–1.35%) |
| All collected posts | 553 | 4 | 4 | 1.45% (0.73–2.83%) |

The 4 high-intent comments are three price questions ("How much is it", "How much is to ship a big dress to San Diego…", "How much can this be so I start saving") and a booking question ("How do I book"), from **4 distinct people**. The 4 medium comments are aspirational ("I will wear a beautiful dress from VJ", "You need to do my wedding gown"). No sales, orders, or conversions are observable in this data.

**Interpretation (hypothesis, not proven):** buying conversations for these brands most likely happen in DMs, on WhatsApp, or on the website, which public scraping cannot see. Ziva's habit of showing prices in captions may also remove the need to ask "how much?". Testing either idea needs DM, WhatsApp, or site data.

### 2. Ranking brands on intent is not defensible

Every brand's in-window rate is 0%, with upper bounds of 3–28%. The ranking changes with scope: across all posts Veekee James leads at 4.1%, but that comes entirely from out-of-window posts. See the sensitivity table in `findings_generated.md`.

### 3. Engagement scale differs about 1,000×, so compare within brands

Median interactions per post in the window: Veekee James ≈ 178,000; Ashluxe 337; WAF Lagos 274 (1 post); Ziva Lagos 43. Per-follower rates are not used for ranking, because follower counts were entered by hand and are unverified.

### 4. Posting time: no robust pattern

Competitors post most often on Saturdays and between 17:00 and 18:00 WAT. Performance by weekday rests on 3–13 posts per day spread across 2–3 brands, which is too few to recommend a posting schedule.

## What a Lagos fashion retailer should do next

**Don't set a platform budget split from this audit.** Instead:

1. **Run a 4–6 week attribution test.** Use a separate WhatsApp number or click-to-chat link, UTM-tagged site links, and a unique discount code per platform (Instagram, TikTok, WhatsApp status). Measure **cost per conversation** and **cost per order**, not likes.
2. **Collect the missing platforms** (TikTok and Facebook) for the same competitors over the same 60 days, with date-based scraping rather than "latest 20".
3. **Track DM volume.** If the retailer's own Instagram inbox is where orders start, export inbox counts weekly. That is the purchase-intent signal public data misses.
4. **A/B test price-in-caption,** Ziva-style, on your own posts. It is cheap and directly measurable through DM and order volume.

## Methodology (short)

ETL in Python (`fashion_intel/`), validated and idempotent. Storage in SQLite or PostgreSQL. Rule-based intent classifier on audience comments, with five documented labels. Sentiment is kept separate. Classifier F1 for the purchase signal on 150 random real comments is **0.67 before tuning** and 0.89 after, with only 4 true positives, so treat both as rough. Full details are in `docs/`.

## Limitations

Instagram only · 4 of 5 brands · uneven window coverage · ~10 comments per post · no follower, DM, sales or spend data · classifier labels not yet human-reviewed · observational data, so no causal claims.
