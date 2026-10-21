# Generated Findings (auto-generated — do not edit by hand)

Run `20261021T140742Z-ab3a5f` · code v2.0.0 · generated 2026-10-21T14:07:44+00:00

## Provenance

- Source file: `apify_raw.csv` (SHA-256 `0d55ca2b43aafc65…`), format `apify_instagram`
- Source file last modified: 2026-05-13T02:48:01 UTC (proxy for collection date; the export has no scrape timestamp)
- Audit window: 2026-03-13 → 2026-05-12 (60 days, UTC)
- Rows: 80 posts, 553 audience comments (566 incl. brand replies); quarantined: 0 posts, 0 comments
- Platforms present: instagram

## Data coverage per competitor (all collected posts)

| display_name | posts_collected | posts_in_window | first_post_wat | last_post_wat | collab_posts | likes_hidden_posts | sampled_audience_comments | reported_comments_total | comment_sample_pct | status |
|---|---|---|---|---|---|---|---|---|---|---|
| Veekee James | 20 | 8 | 2024-01-14 | 2026-05-10 | 5 | 3 | 195 | 88,382 | 0.22 | thin: <10 posts in window |
| Ashluxe | 20 | 20 | 2026-03-17 | 2026-04-29 | 0 | 0 | 117 | 193 | 60.62 | ok |
| WAF Lagos | 20 | 1 | 2025-08-23 | 2026-04-03 | 7 | 1 | 166 | 729 | 22.77 | thin: <10 posts in window |
| Ziva Lagos | 20 | 20 | 2026-04-16 | 2026-05-12 | 2 | 0 | 75 | 202 | 37.13 | ok |
| Yomi Casual | 0 | 0 | – | – | 0 | 0 | 0 | – | – | no data collected |

`comment_sample_pct` = sampled audience comments ÷ comment total reported by Instagram. The scraper returns only the ~10 latest comments per post.

## Audience purchase-intent signals by brand (audit window)

Denominator: sampled audience comments on in-window posts. `hm` = high + medium. CI = 95% Wilson interval for the high+medium rate.

| brand_handle | sampled_comments | high | medium | low | uncertain | no_signal | high_rate_pct | high_or_medium_rate_pct | hm_ci_low | hm_ci_high | high_intent_commenters | posts_with_high | posts_with_sampled_comments |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ashluxe | 117 | 0 | 0 | 28 | 0 | 89 | 0 | 0 | 0 | 3.18 | 0 | 0 | 19 |
| veekeejames_official | 78 | 0 | 0 | 32 | 0 | 46 | 0 | 0 | 0 | 4.69 | 0 | 0 | 8 |
| wflsncrm | 10 | 0 | 0 | 1 | 0 | 9 | 0 | 0 | 0 | 27.75 | 0 | 0 | 1 |
| zivalagos | 75 | 0 | 0 | 23 | 1 | 51 | 0 | 0 | 0 | 4.87 | 0 | 0 | 18 |

## By platform (audit window)

| platform | sampled_comments | high | medium | high_or_medium_rate_pct | hm_ci_low | hm_ci_high |
|---|---|---|---|---|---|---|
| instagram | 280 | 0 | 0 | 0 | 0 | 1.35 |

_A platform comparison needs at least two platforms. Only the platforms listed above were collected._

## Sensitivity: high+medium rate and rank under different data choices

| scenario | brand_handle | sampled_comments | high | medium | high_or_medium_rate_pct | hm_ci_low | hm_ci_high | rank_high_or_medium |
|---|---|---|---|---|---|---|---|---|
| audit_window (primary) | ashluxe | 117 | 0 | 0 | 0 | 0 | 3.18 | 1 |
| audit_window (primary) | veekeejames_official | 78 | 0 | 0 | 0 | 0 | 4.69 | 1 |
| audit_window (primary) | wflsncrm | 10 | 0 | 0 | 0 | 0 | 27.75 | 1 |
| audit_window (primary) | zivalagos | 75 | 0 | 0 | 0 | 0 | 4.87 | 1 |
| all_collected_posts | ashluxe | 117 | 0 | 0 | 0 | 0 | 3.18 | 2 |
| all_collected_posts | veekeejames_official | 195 | 4 | 4 | 4.1 | 2.09 | 7.89 | 1 |
| all_collected_posts | wflsncrm | 166 | 0 | 0 | 0 | 0 | 2.26 | 2 |
| all_collected_posts | zivalagos | 75 | 0 | 0 | 0 | 0 | 4.87 | 2 |
| window_excl_collab | ashluxe | 117 | 0 | 0 | 0 | 0 | 3.18 | 1 |
| window_excl_collab | veekeejames_official | 38 | 0 | 0 | 0 | 0 | 9.18 | 1 |
| window_excl_collab | wflsncrm | 10 | 0 | 0 | 0 | 0 | 27.75 | 1 |
| window_excl_collab | zivalagos | 72 | 0 | 0 | 0 | 0 | 5.07 | 1 |
| window_excl_pinned | ashluxe | 117 | 0 | 0 | 0 | 0 | 3.18 | 1 |
| window_excl_pinned | veekeejames_official | 78 | 0 | 0 | 0 | 0 | 4.69 | 1 |
| window_excl_pinned | wflsncrm | 10 | 0 | 0 | 0 | 0 | 27.75 | 1 |
| window_excl_pinned | zivalagos | 72 | 0 | 0 | 0 | 0 | 5.07 | 1 |
| window_text_comments_only | ashluxe | 63 | 0 | 0 | 0 | 0 | 5.75 | 1 |
| window_text_comments_only | veekeejames_official | 45 | 0 | 0 | 0 | 0 | 7.87 | 1 |
| window_text_comments_only | wflsncrm | 7 | 0 | 0 | 0 | 0 | 35.43 | 1 |
| window_text_comments_only | zivalagos | 33 | 0 | 0 | 0 | 0 | 10.43 | 1 |

## Engagement by brand (audit window; medians, hidden likes excluded)

| brand_handle | posts | posts_likes_known | median_likes | median_comments | median_interactions | median_likes_per_1k_followers | median_video_views |
|---|---|---|---|---|---|---|---|
| ashluxe | 20 | 20 | 329.5 | 6.5 | 337 | 2.2 | 6,755 |
| veekeejames_official | 8 | 5 | 174,794 | 5,496.5 | 178,415 | 87.4 | 837,443.5 |
| wflsncrm | 1 | 1 | 255 | 19 | 274 | 10.2 | – |
| zivalagos | 20 | 20 | 36 | 5 | 43 | 0.47 | 1,008 |

`median_likes_per_1k_followers` uses manually entered, unverified follower counts — reference only.

## Seller-side caption behaviour (audit window; % of posts)

| brand_handle | posts | shows_price_pct | call_to_action_pct | launch_or_restock_pct |
|---|---|---|---|---|
| ashluxe | 20 | 0 | 5 | 0 |
| veekeejames_official | 8 | 0 | 0 | 0 |
| wflsncrm | 1 | 0 | 0 | 0 |
| zivalagos | 20 | 65 | 75 | 30 |

## Posting day (audit window, Lagos time)

`median_relative_performance` = post interactions ÷ that brand's median (1.0 = typical).

| published_weekday_wat | posts | brands | median_relative_performance |
|---|---|---|---|
| Monday | 4 | 2 | 1.08 |
| Tuesday | 7 | 2 | 1.67 |
| Wednesday | 7 | 2 | 1.17 |
| Thursday | 7 | 2 | 0.91 |
| Friday | 5 | 3 | 0.67 |
| Saturday | 13 | 3 | 1 |
| Sunday | 3 | 2 | 0.95 |

## Data-quality issues

| table | check | severity | count | detail |
|---|---|---|---|---|
| source | scraper_error_row | warning | 1 | yomicasual: no_items - Empty or private data for provided input |
| posts | empty_caption | info | 1 |  |
| posts | likes_hidden_by_platform | info | 4 | stored as NULL, not 0 |
| posts | collab_post | info | 14 | owned by another account but shown on the competitor's grid |
| comments | empty_text | info | 1 |  |
| comments | account_reply | info | 15 | brand/collaborator replies excluded from audience metrics |
| comments | duplicate_comment_id | warning | 4 | deduplicated |

## What these numbers cannot show

- Sales, conversions or revenue: none were observed. A `high` comment is a purchase-intent *signal*.
- Causality: differences between brands are observational and confounded by audience size, content and niche.
- Budget allocation across platforms: requires data from more than one platform plus spend/conversion data.
