# Data Dictionary and Metric Definitions

`NULL`/empty always means **unknown**. It never means zero.

## `posts` (data/processed/posts.csv · table `social_posts`)

| Column | Type | Meaning |
|---|---|---|
| `post_id` | text, PK | `<platform>:<shortcode>`, a stable ID used for dedupe and upserts |
| `platform` | text | Canonical platform: `instagram`, `tiktok`, `facebook`, `x`, `youtube` |
| `brand_handle` | text, FK | Competitor whose profile was scraped (from Apify `inputUrl`) |
| `display_name` | text | From `config/brands.json` |
| `brand_in_registry` | bool | Brand is one of the configured competitors |
| `owner_username` | text | Account that actually owns the post |
| `is_collab` | bool | `owner_username` ≠ `brand_handle` (collab or partner post on the competitor's grid) |
| `is_pinned` | bool | Pinned to the top of the profile (often old) |
| `post_url`, `shortcode` | text | Canonical URL (https, no query string) |
| `post_type` | text | `clips` (Reel), `Sidecar` (carousel), `Image`, `Video` |
| `caption` | text | Normalised caption ('' if none) |
| `published_at_utc` | timestamp | Publication time, UTC |
| `published_date_wat`, `published_hour_wat`, `published_weekday_wat` | text / int / text | Same moment in Lagos time (WAT = UTC+1) |
| `in_audit_window` | bool | Published inside the audit window (default: 60 days ending at the newest competitor post) |
| `likes` | int, nullable | Like count. NULL when hidden by Instagram (`-1`) or missing |
| `likes_hidden` | bool | Instagram reported hidden likes |
| `comments_count` | int, nullable | Total comments reported by Instagram (not the sample size) |
| `interactions` | int, nullable | `likes + comments_count`, NULL if either is unknown |
| `video_views`, `video_plays` | int, nullable | Reels/videos only |
| `follower_count_reference` | int, nullable | Manual value from `config/brands.json` (unverified) |
| `likes_per_1k_followers` | float, nullable | `likes / follower_count_reference × 1000`, **reference only** |
| `caption_shows_price` / `caption_call_to_action` / `caption_launch_or_restock` | bool | **Seller-side** caption behaviour (₦ price, "shop/DM to order/link in bio", "new collection/restock") |
| `data_source`, `source_file`, `source_sha256`, `source_row`, `file_modified_at_utc`, `extracted_at_utc` | text / int | Provenance |

## `comments` (data/processed/comments.csv · table `audience_comments`)

| Column | Type | Meaning |
|---|---|---|
| `comment_id` | text, PK | `instagram:c:<instagram comment id>` |
| `post_id` | text, FK | Post the comment is on |
| `parent_comment_id`, `is_reply` | text / bool | Replies to another comment |
| `commenter_id` | text | Pseudonymised commenter (`user_<hash>`). Real handles are never stored |
| `is_account_reply` | bool | Written by the competitor, the post owner or a co-author |
| `is_audience` | bool | `not is_account_reply`. Only these count in intent metrics |
| `text` | text | Normalised comment text |
| `published_*` | | As for posts |
| `post_in_audit_window`, `post_is_collab` | bool | Copied from the parent post |
| `intent_label` | text | `high`, `medium`, `low`, `uncertain`, `no_signal` (see `intent_taxonomy.md`) |
| `intent_signals` | text | Pipe-separated rule tags, e.g. `price_inquiry\|compliment` |
| `intent_signal_count` | int | Distinct purchase-signal types (high + medium tags) in the comment. Repeats count once |
| `intent_reason` | text | Plain-English reason for the label |
| `intent_negated`, `affordability_barrier`, `post_purchase_feedback` | bool | Rule flags |
| `sentiment_polarity`, `sentiment_label` | float / text | TextBlob + emoji heuristic. **Independent of intent** |

## Metric definitions

All metrics live in `fashion_intel/metrics.py`. Their SQL equivalents are in `sql/`, and tests assert they agree.

| Metric | Definition | Denominator |
|---|---|---|
| Sampled audience comments | Count of `is_audience` comments on in-scope posts | – |
| High-intent rate | high ÷ sampled comments × 100 | sampled audience comments, **including emoji-only** |
| High + medium (shopping-signal) rate | (high + medium) ÷ sampled comments × 100, with 95% Wilson CI | same |
| Signals per 100 comments | Σ `intent_signal_count` ÷ sampled comments × 100 | same |
| High-intent commenters | distinct `commenter_id` with ≥1 high comment (people, not comments) | – |
| Posts with high intent % | posts with ≥1 high comment ÷ posts with ≥1 sampled comment | posts with sampled comments |
| Median likes / comments / interactions | median per post | posts where the value is known |
| Relative performance | post interactions ÷ that brand's median interactions; median per time bucket | posts with known interactions |
| Comment sample % | sampled audience comments ÷ Σ reported `comments_count` | reported comment totals |
| Caption signal % | posts with the caption signal ÷ posts | posts |

**Signal ≠ person ≠ transaction.** A *signal* is one classified comment. A *person* is a distinct commenter. A *transaction* is a verified purchase, and this dataset contains **none**.

**Why medians:** one Veekee James Reel has 535,685 likes. Means are dominated by single viral posts.

**Why no follower-based ranking:** follower counts were typed in by hand, are rounded, and have no date.
