-- intent_analysis.sql
-- Audience purchase-intent signals per competitor (one row per brand).
-- Unit: one sampled audience comment (brand/collaborator replies excluded).
-- Denominator for every *_rate_pct: sampled_comments in that brand's scope.
-- A "high" comment is a purchase-intent SIGNAL, not a purchase or a conversion.
SELECT
    p.brand_handle,
    COUNT(*)                                                         AS sampled_comments,
    SUM(CASE WHEN c.intent_label = 'high'      THEN 1 ELSE 0 END)    AS high,
    SUM(CASE WHEN c.intent_label = 'medium'    THEN 1 ELSE 0 END)    AS medium,
    SUM(CASE WHEN c.intent_label = 'low'       THEN 1 ELSE 0 END)    AS low,
    SUM(CASE WHEN c.intent_label = 'uncertain' THEN 1 ELSE 0 END)    AS uncertain,
    SUM(CASE WHEN c.intent_label = 'no_signal' THEN 1 ELSE 0 END)    AS no_signal,
    ROUND(100.0 * SUM(CASE WHEN c.intent_label = 'high' THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 2)                                  AS high_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN c.intent_label IN ('high', 'medium') THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 2)                                  AS high_or_medium_rate_pct,
    ROUND(100.0 * SUM(c.intent_signal_count) / NULLIF(COUNT(*), 0), 2) AS signals_per_100_comments,
    COUNT(DISTINCT CASE WHEN c.intent_label = 'high' THEN c.commenter_id END) AS high_intent_commenters,
    COUNT(DISTINCT CASE WHEN c.intent_label = 'high' THEN c.post_id END)      AS posts_with_high
FROM audience_comments AS c
JOIN social_posts      AS p ON p.post_id = c.post_id
JOIN competitor_brands AS b ON b.brand_handle = p.brand_handle
WHERE c.is_audience = TRUE
  AND b.in_registry = TRUE
  AND (:include_all = 1 OR p.in_audit_window = TRUE)
GROUP BY p.brand_handle
ORDER BY high_or_medium_rate_pct DESC, p.brand_handle;
