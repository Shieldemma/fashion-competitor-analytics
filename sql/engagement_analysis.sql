-- engagement_analysis.sql
-- Engagement by competitor and post format (Reel/clips, Sidecar carousel, Image).
-- Denominator for each average = posts where that metric is known (NULLs skipped by AVG).
-- Follower-based rates are deliberately omitted: follower counts are manual reference values.
SELECT
    p.brand_handle,
    COALESCE(p.post_type, 'unknown')   AS post_type,
    COUNT(*)                           AS posts,
    COUNT(p.likes)                     AS posts_likes_known,
    ROUND(AVG(p.likes), 1)             AS avg_likes,
    ROUND(AVG(p.comments_count), 1)    AS avg_comments,
    COUNT(p.video_views)               AS posts_with_views,
    ROUND(AVG(p.video_views), 1)       AS avg_video_views
FROM social_posts AS p
JOIN competitor_brands AS b ON b.brand_handle = p.brand_handle
WHERE b.in_registry = TRUE
  AND (:include_all = 1 OR p.in_audit_window = TRUE)
GROUP BY p.brand_handle, COALESCE(p.post_type, 'unknown')
ORDER BY p.brand_handle, posts DESC;
