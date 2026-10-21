-- top_brands.sql
-- Post volume and engagement per competitor.
-- Scope: registered competitors; posts inside the audit window unless the include_all parameter = 1.
-- Denominators:
--   avg_likes        = posts whose like count is known (hidden likes are NULL, so AVG skips them)
--   avg_interactions = posts where likes AND comments are both known
-- Medians are computed in Python (fashion_intel/metrics.py) because SQLite has no MEDIAN.
SELECT
    p.brand_handle,
    b.display_name,
    COUNT(*)                                      AS posts,
    COUNT(p.likes)                                AS posts_likes_known,
    SUM(CASE WHEN p.likes_hidden THEN 1 ELSE 0 END) AS posts_likes_hidden,
    ROUND(AVG(p.likes), 1)                        AS avg_likes,
    ROUND(AVG(p.comments_count), 1)               AS avg_comments,
    ROUND(AVG(p.interactions), 1)                 AS avg_interactions,
    SUM(CASE WHEN p.is_collab THEN 1 ELSE 0 END)  AS collab_posts
FROM social_posts AS p
JOIN competitor_brands AS b ON b.brand_handle = p.brand_handle
WHERE b.in_registry = TRUE
  AND (:include_all = 1 OR p.in_audit_window = TRUE)
GROUP BY p.brand_handle, b.display_name
ORDER BY posts DESC, p.brand_handle;
