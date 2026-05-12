SELECT
    brand_handle,
    COUNT(*) AS total_posts,
    ROUND(AVG(likes), 2) AS avg_likes,
    ROUND(AVG(engagement_rate), 4) AS avg_engagement
FROM posts
GROUP BY brand_handle
ORDER BY avg_engagement DESC;
