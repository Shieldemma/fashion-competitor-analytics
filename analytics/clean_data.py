# analytics/clean_data.py
# Run with:
# python analytics/clean_data.py

import pandas as pd
import os

print("Starting data cleaning pipeline...")

# ── Load raw data ─────────────────────────────────────────────

input_path = "data/raw/instagram_posts.csv"

if not os.path.exists(input_path):
    print(f"ERROR: {input_path} not found.")
    print("Run scraper first.")
    exit()

df = pd.read_csv(input_path)

print(f"Raw rows loaded: {len(df)}")
print(f"Columns: {list(df.columns)}\n")

original_count = len(df)

# ── Remove duplicate posts ───────────────────────────────────

df = df.drop_duplicates(subset=["post_url"])

print(
    f"After removing duplicates: "
    f"{len(df)} rows "
    f"(removed {original_count - len(df)})"
)

# ── Clean captions safely ────────────────────────────────────

df["caption"] = df["caption"].fillna("").astype(str)

# IMPORTANT:
# We are NOT dropping empty captions for now because
# Instagram scraping is incomplete.
# This keeps the pipeline alive.

print("Caption column cleaned.")

# ── Clean likes ──────────────────────────────────────────────

def clean_likes(value):

    value = str(value).strip().replace(",", "")

    value_lower = value.lower()

    try:

        if "m" in value_lower:
            return int(float(value_lower.replace("m", "")) * 1_000_000)

        elif "k" in value_lower:
            return int(float(value_lower.replace("k", "")) * 1_000)

        else:
            return int(float(value))

    except:
        return 0

df["likes"] = df["likes"].apply(clean_likes)

print(
    f"Likes cleaned. "
    f"Range: {df['likes'].min()} – {df['likes'].max()}"
)

# ── Followers cleanup ────────────────────────────────────────

FALLBACK_FOLLOWERS = {
    "veekeejames_official": 2000000,
    "ashluxe": 150000,
    "wflsncrm": 25000,
    "zivalagos": 80000,
    "yomicasual": 500000,
}

if "followers" not in df.columns:

    df["followers"] = df["brand"].map(FALLBACK_FOLLOWERS)

df["followers"] = pd.to_numeric(
    df["followers"],
    errors="coerce"
).fillna(10000)

# ── Engagement rate ──────────────────────────────────────────

df["engagement_rate"] = (
    df["likes"] / df["followers"] * 100
).round(4)

# ── Post date cleanup ────────────────────────────────────────

if "post_date" in df.columns:

    df["post_date"] = pd.to_datetime(
        df["post_date"],
        errors="coerce"
    )

    df["post_hour"] = df["post_date"].dt.hour

    df["post_day"] = df["post_date"].dt.day_name()

# ── Purchase intent classification ───────────────────────────

HIGH_INTENT_PHRASES = [
    "price",
    "how much",
    "how to order",
    "do you deliver",
    "dm to order",
    "can i buy",
    "payment",
    "whatsapp",
    "available in my size",
    "send me the link"
]

MEDIUM_INTENT_WORDS = [
    "available",
    "delivery",
    "order",
    "buy",
    "dm",
    "size",
    "stock",
    "restock",
    "link",
    "colour",
    "color"
]

def classify_intent(text):

    text = str(text).lower()

    for phrase in HIGH_INTENT_PHRASES:

        if phrase in text:
            return "High Intent"

    for word in MEDIUM_INTENT_WORDS:

        if word in text:
            return "Medium Intent"

    return "Low Intent"

df["has_intent_signal"] = df["caption"].apply(

    lambda x: any(
        w in str(x).lower()
        for w in HIGH_INTENT_PHRASES + MEDIUM_INTENT_WORDS
    )
)

df["intent_tier"] = df["caption"].apply(classify_intent)

# ── Summary ──────────────────────────────────────────────────

print("\n=== Cleaning complete ===")

print(
    df[
        [
            "brand",
            "likes",
            "engagement_rate",
            "intent_tier"
        ]
    ].head()
)

print("\n=== Intent distribution ===")

print(df["intent_tier"].value_counts())

print("\n=== Brand breakdown ===")

print(
    df.groupby("brand").agg(
        posts=("brand", "count"),
        avg_likes=("likes", "mean"),
        avg_engagement=("engagement_rate", "mean")
    ).round(4)
)

# ── Save cleaned dataset ─────────────────────────────────────

os.makedirs("data/cleaned", exist_ok=True)

output_path = "data/cleaned/cleaned_posts.csv"

df.to_csv(output_path, index=False)

print(f"\n✓ Saved {len(df)} clean rows to {output_path}")
