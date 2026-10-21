-- platform_intent.sql
-- The client's core question: which platform shows the strongest purchase-intent signals?
-- Same definitions and denominators as intent_analysis.sql, grouped by platform.
-- With the current data only Instagram is present, so this cannot rank platforms.
SELECT
    p.platform,
    COUNT(DISTINCT p.brand_handle)                                   AS brands,
    COUNT(DISTINCT p.post_id)                                        AS posts_with_sampled_comments,
    COUNT(*)                                                         AS sampled_comments,
    SUM(CASE WHEN c.intent_label = 'high' THEN 1 ELSE 0 END)         AS high,
    SUM(CASE WHEN c.intent_label = 'medium' THEN 1 ELSE 0 END)       AS medium,
    ROUND(100.0 * SUM(CASE WHEN c.intent_label IN ('high', 'medium') THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 2)                                  AS high_or_medium_rate_pct
FROM audience_comments AS c
JOIN social_posts      AS p ON p.post_id = c.post_id
JOIN competitor_brands AS b ON b.brand_handle = p.brand_handle
WHERE c.is_audience = TRUE
  AND b.in_registry = TRUE
  AND (:include_all = 1 OR p.in_audit_window = TRUE)
GROUP BY p.platform
ORDER BY p.platform;
