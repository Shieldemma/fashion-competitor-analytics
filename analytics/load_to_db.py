# analytics/load_to_db.py
# Run this with: python analytics/load_to_db.py
#
# Purpose:
#   Load cleaned competitor analytics data into PostgreSQL
#   using a clean-reload ETL strategy.
#
# Pipeline:
#   cleaned CSV -> PostgreSQL -> verification queries
#
# Requirements:
#   - PostgreSQL running locally
#   - fashiondb database already created
#   - schema.sql already executed
#   - cleaned_posts.csv already generated

from sqlalchemy import create_engine, text
import pandas as pd
import os

# ── DATABASE CONFIG ───────────────────────────────────────────────────────────
DB_USER = "ifureemmanueludo"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "fashiondb"

DB_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("\nConnecting to PostgreSQL...\n")

# ── CREATE DATABASE ENGINE ───────────────────────────────────────────────────
try:
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
        future=True
    )

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print("✓ Connected to fashiondb successfully")

except Exception as e:
    print(f"✗ Database connection failed:\n{e}")

    print("\nTroubleshooting:")
    print("1. Make sure Postgres.app is running")
    print("2. Verify fashiondb exists")
    print("3. Verify DB_USER matches your Mac username")
    print("4. Test manually:")
    print("   psql fashiondb")

    raise SystemExit(1)

# ── LOAD CLEANED DATA ─────────────────────────────────────────────────────────
cleaned_path = "data/cleaned/cleaned_posts.csv"

if not os.path.exists(cleaned_path):
    print(f"\n✗ Missing file: {cleaned_path}")
    print("Run first:")
    print("python analytics/clean_data.py")

    raise SystemExit(1)

df = pd.read_csv(cleaned_path)

print(f"\nLoaded {len(df)} cleaned posts")

# ── STANDARDIZE COLUMN NAMES ─────────────────────────────────────────────────
df_db = df.rename(columns={
    "brand": "brand_handle",
    "has_intent_signal": "has_intent"
})

# ── KEEP ONLY DATABASE COLUMNS ───────────────────────────────────────────────
db_columns = [
    "brand_handle",
    "platform",
    "post_url",
    "caption",
    "likes",
    "engagement_rate",
    "intent_tier",
    "has_intent",
    "post_date",
    "post_hour",
    "post_day"
]

available_columns = [c for c in db_columns if c in df_db.columns]
df_db = df_db[available_columns]

print("\nColumns being inserted:")
print(list(df_db.columns))

# ── DATA TYPE CLEANUP ────────────────────────────────────────────────────────
if "has_intent" in df_db.columns:
    df_db["has_intent"] = (
        df_db["has_intent"]
        .fillna(False)
        .astype(bool)
    )

numeric_cols = ["likes", "engagement_rate", "post_hour"]

for col in numeric_cols:
    if col in df_db.columns:
        df_db[col] = pd.to_numeric(
            df_db[col],
            errors="coerce"
        )

if "post_date" in df_db.columns:
    df_db["post_date"] = pd.to_datetime(
        df_db["post_date"],
        errors="coerce"
    )

# Replace pandas NaN with Python None
df_db = df_db.where(pd.notnull(df_db), None)

# ── REMOVE OLD DATA BEFORE INSERT ────────────────────────────────────────────
# This prevents duplicate rows every time the pipeline runs.

try:
    with engine.begin() as conn:
        deleted = conn.execute(
            text("DELETE FROM posts")
        )

    print("\n✓ Cleared old rows from posts table")

except Exception as e:
    print(f"\n✗ Failed clearing old rows:\n{e}")
    raise SystemExit(1)

# ── INSERT DATA ──────────────────────────────────────────────────────────────
try:
    df_db.to_sql(
        name="posts",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=100
    )

    print(f"\n✓ Successfully inserted {len(df_db)} rows")

except Exception as e:
    print(f"\n✗ Insert failed:\n{e}")

    print("\nPossible causes:")
    print("- Schema mismatch")
    print("- Invalid data types")
    print("- Database permission issue")

    raise SystemExit(1)

# ── VERIFICATION QUERIES ─────────────────────────────────────────────────────
print("\nRunning verification queries...\n")

with engine.connect() as conn:

    # Total rows
    total_posts = conn.execute(
        text("SELECT COUNT(*) FROM posts")
    ).scalar()

    print(f"✓ Total posts in database: {total_posts}")

    # Brand analytics
    result = conn.execute(text("""
        SELECT
            b.name,
            COUNT(p.id) AS post_count,
            ROUND(AVG(p.likes), 2) AS avg_likes,
            ROUND(AVG(p.engagement_rate), 4) AS avg_engagement
        FROM posts p
        JOIN brands b
            ON p.brand_handle = b.handle
        GROUP BY b.name
        ORDER BY avg_engagement DESC
    """))

    print("\n=== Brand Performance Summary ===\n")

    for row in result:
        print(
            f"{row.name:<15} | "
            f"Posts: {row.post_count:<3} | "
            f"Avg Likes: {row.avg_likes:<10} | "
            f"Avg Engagement: {row.avg_engagement}%"
        )

    # Platform comparison
    platform_result = conn.execute(text("""
        SELECT
            platform,
            COUNT(*) AS total_posts,
            ROUND(AVG(engagement_rate), 4) AS avg_engagement
        FROM posts
        GROUP BY platform
        ORDER BY avg_engagement DESC
    """))

    print("\n=== Platform Performance ===\n")

    for row in platform_result:
        print(
            f"{row.platform:<10} | "
            f"Posts: {row.total_posts:<3} | "
            f"Avg Engagement: {row.avg_engagement}%"
        )

print("\n✓ Database ETL pipeline completed successfully")