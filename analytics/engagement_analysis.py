# analytics/engagement_analysis.py
# Run this with: python analytics/engagement_analysis.py
# Answers the 7 core business questions with Python + SQL

from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
import os

# ── DATABASE CONNECTION ───────────────────────────────────────────────────────
DB_USER     = "postgres"
DB_PASSWORD = "password"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "fashiondb"

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

os.makedirs("data/processed", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# ── PULL ALL DATA ─────────────────────────────────────────────────────────────
df = pd.read_sql("""
    SELECT
        p.*,
        b.name AS brand_name,
        b.followers AS brand_followers
    FROM posts p
    JOIN brands b ON p.brand_handle = b.handle
""", engine)

print(f"Loaded {len(df)} posts from database\n")

# ── BUSINESS QUESTION 1: Which brand has highest engagement? ──────────────────
print("=" * 55)
print("Q1: Which competitor has the highest engagement rate?")
print("=" * 55)

brand_summary = df.groupby("brand_name").agg(
    avg_engagement_rate=("engagement_rate", "mean"),
    total_posts=("id", "count"),
    total_likes=("likes", "sum"),
    median_likes=("likes", "median")
).round(4).sort_values("avg_engagement_rate", ascending=False)

print(brand_summary.to_string())

# ── BUSINESS QUESTION 2: Which platform drives purchase intent? ───────────────
print("\n" + "=" * 55)
print("Q2: Which platform drives the most purchase intent?")
print("=" * 55)

platform_intent = pd.read_sql("""
    SELECT
        platform,
        COUNT(*) FILTER (WHERE intent_tier = 'High Intent')   AS high_intent,
        COUNT(*) FILTER (WHERE intent_tier = 'Medium Intent') AS medium_intent,
        COUNT(*) FILTER (WHERE intent_tier = 'Low Intent')    AS low_intent,
        COUNT(*)                                               AS total_posts,
        ROUND(
            COUNT(*) FILTER (WHERE intent_tier = 'High Intent')
            * 100.0 / NULLIF(COUNT(*), 0), 2
        ) AS high_intent_rate_pct
    FROM posts
    GROUP BY platform
    ORDER BY high_intent_rate_pct DESC
""", engine)

print(platform_intent.to_string(index=False))

# ── BUSINESS QUESTION 3: What content type performs best? ─────────────────────
print("\n" + "=" * 55)
print("Q3: Which content generates most engagement?")
print("=" * 55)

# Classify captions as product-push, storytelling, or general
def content_type(caption):
    cap = str(caption).lower()
    if any(w in cap for w in ["new", "collection", "drop", "available", "shop", "order"]):
        return "Product Push"
    elif any(w in cap for w in ["story", "journey", "behind", "making", "process", "meet"]):
        return "Storytelling"
    elif any(w in cap for w in ["congratulations", "celebrate", "thank", "love", "grateful"]):
        return "Community"
    else:
        return "General"

df["content_type"] = df["caption"].apply(content_type)

content_perf = df.groupby("content_type").agg(
    avg_engagement=("engagement_rate", "mean"),
    post_count=("id", "count")
).round(4).sort_values("avg_engagement", ascending=False)

print(content_perf.to_string())

# ── BUSINESS QUESTION 4: What posting time generates most engagement? ──────────
print("\n" + "=" * 55)
print("Q4: What posting times generate the most engagement?")
print("=" * 55)

if "post_hour" in df.columns and df["post_hour"].notna().sum() > 0:
    hour_perf = df.groupby("post_hour").agg(
        avg_likes=("likes", "mean"),
        post_count=("id", "count")
    ).round(0).sort_values("avg_likes", ascending=False)
    print(hour_perf.head(5).to_string())
else:
    print("Post time data not available (Instagram did not provide timestamps)")
    print("This is common — supplement with manual observation or paid tools")

# ── BUSINESS QUESTION 5: Which competitor has most customer interaction? ────────
print("\n" + "=" * 55)
print("Q5: Which competitor has the highest customer interaction?")
print("=" * 55)

interaction = df.groupby("brand_name").agg(
    total_likes=("likes", "sum"),
    avg_likes_per_post=("likes", "mean"),
    intent_posts=("has_intent", "sum")
).round(0).sort_values("total_likes", ascending=False)

print(interaction.to_string())

# ── SAVE SUMMARY ──────────────────────────────────────────────────────────────
brand_summary.to_csv("data/processed/brand_summary.csv")
platform_intent.to_csv("data/processed/platform_intent.csv", index=False)
df.to_csv("data/processed/full_analysis.csv", index=False)

print("\n✓ Saved analysis files to data/processed/")

# ── QUICK CHARTS ──────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Chart 1: Engagement by brand
brand_summary["avg_engagement_rate"].sort_values().plot(
    kind="barh", ax=axes[0],
    color=["#E24B4A","#1D9E75","#378ADD","#BA7517","#7F77DD"]
)
axes[0].set_title("Average engagement rate by brand")
axes[0].set_xlabel("Engagement rate (%)")

# Chart 2: Intent distribution by brand
intent_by_brand = df.groupby(["brand_name", "intent_tier"]).size().unstack(fill_value=0)
intent_by_brand.plot(
    kind="bar", ax=axes[1],
    color=["#E24B4A","#1D9E75","#888780"]
)
axes[1].set_title("Purchase intent by brand")
axes[1].set_xlabel("")
axes[1].tick_params(axis="x", rotation=30)

plt.tight_layout()
plt.savefig("reports/engagement_charts.png", dpi=150, bbox_inches="tight")
plt.show()

print("✓ Charts saved to reports/engagement_charts.png")
