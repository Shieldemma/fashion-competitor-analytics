-- posting_times.sql
-- When do competitors post? Lagos local time (WAT = UTC+1).
-- Counts only. Performance-by-time uses a within-brand relative index in Python
-- (metrics.posting_time_summary) because brands differ ~1000x in audience size.
SELECT
    p.published_weekday_wat         AS weekday,
    p.published_hour_wat            AS hour_wat,
    COUNT(*)                        AS posts,
    COUNT(DISTINCT p.brand_handle)  AS brands
FROM social_posts AS p
JOIN competitor_brands AS b ON b.brand_handle = p.brand_handle
WHERE b.in_registry = TRUE
  AND p.published_hour_wat IS NOT NULL
  AND (:include_all = 1 OR p.in_audit_window = TRUE)
GROUP BY p.published_weekday_wat, p.published_hour_wat
ORDER BY posts DESC, weekday, hour_wat;
