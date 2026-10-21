-- data_coverage.sql
-- What data do we actually have per registered competitor? Brands with no posts still appear.
SELECT
    b.brand_handle,
    b.display_name,
    COUNT(p.post_id)                                                AS posts_collected,
    SUM(CASE WHEN p.in_audit_window THEN 1 ELSE 0 END)              AS posts_in_window,
    MIN(p.published_date_wat)                                       AS first_post_wat,
    MAX(p.published_date_wat)                                       AS last_post_wat,
    SUM(CASE WHEN p.is_collab THEN 1 ELSE 0 END)                    AS collab_posts,
    SUM(CASE WHEN p.likes_hidden THEN 1 ELSE 0 END)                 AS likes_hidden_posts
FROM competitor_brands AS b
LEFT JOIN social_posts AS p ON p.brand_handle = b.brand_handle
WHERE b.in_registry = TRUE
GROUP BY b.brand_handle, b.display_name
ORDER BY posts_collected DESC, b.brand_handle;
