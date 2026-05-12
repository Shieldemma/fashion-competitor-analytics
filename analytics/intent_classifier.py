# analytics/intent_classifier.py
# Run this with: python analytics/intent_classifier.py
# Input:  data/cleaned/cleaned_posts.csv
# Output: data/processed/intent_classified.csv

import pandas as pd
from textblob import TextBlob
import os

print("Running purchase intent classifier...\n")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
input_path = "data/cleaned/cleaned_posts.csv"

if not os.path.exists(input_path):
    print(f"ERROR: {input_path} not found")
    print("Run clean_data.py first: python analytics/clean_data.py")
    exit()

df = pd.read_csv(input_path)
print(f"Loaded {len(df)} posts")

# ── INTENT KEYWORD LISTS ──────────────────────────────────────────────────────
# These are Lagos-specific buying signal phrases
HIGH_INTENT_PHRASES = [
    "price", "how much", "how to order", "do you deliver",
    "dm to order", "can i buy", "payment", "whatsapp",
    "available in my size", "send me the link", "cost",
    "where can i get", "can i order", "inbox", "ping me"
]

MEDIUM_INTENT_WORDS = [
    "available", "delivery", "order", "buy", "dm",
    "size", "stock", "restock", "link", "colour",
    "color", "colour", "shop", "purchase"
]

LOW_INTENT_WORDS = [
    "love", "beautiful", "gorgeous", "fire", "want",
    "need this", "goals", "stunning", "amazing", "wow",
    "insane", "this is everything", "obsessed"
]

# ── CLASSIFIERS ───────────────────────────────────────────────────────────────
def classify_intent(text):
    text = str(text).lower()
    for phrase in HIGH_INTENT_PHRASES:
        if phrase in text:
            return "High Intent"
    for word in MEDIUM_INTENT_WORDS:
        if word in text:
            return "Medium Intent"
    for word in LOW_INTENT_WORDS:
        if word in text:
            return "Low Intent"
    return "No Signal"

def get_sentiment(text):
    try:
        polarity = TextBlob(str(text)).sentiment.polarity
        if polarity > 0.2:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"
    except:
        return "neutral"

def count_intent_phrases(text):
    text = str(text).lower()
    count = sum(1 for phrase in HIGH_INTENT_PHRASES if phrase in text)
    count += sum(1 for word in MEDIUM_INTENT_WORDS if word in text)
    return count

# ── APPLY TO DATASET ──────────────────────────────────────────────────────────
print("Classifying captions...")
df["intent_tier"]    = df["caption"].apply(classify_intent)
df["sentiment"]      = df["caption"].apply(get_sentiment)
df["intent_signals"] = df["caption"].apply(count_intent_phrases)

# ── RESULTS SUMMARY ───────────────────────────────────────────────────────────
print("\n=== Purchase Intent Distribution ===")
print(df["intent_tier"].value_counts())

print("\n=== Intent by Brand ===")
intent_by_brand = df.groupby(["brand", "intent_tier"]).size().unstack(fill_value=0)
print(intent_by_brand.to_string())

print("\n=== Sentiment by Brand ===")
sentiment_by_brand = df.groupby(["brand", "sentiment"]).size().unstack(fill_value=0)
print(sentiment_by_brand.to_string())

print("\n=== Top 10 High-Intent Posts ===")
high_intent = df[df["intent_tier"] == "High Intent"].sort_values(
    "likes", ascending=False
)[["brand", "likes", "caption", "intent_tier"]].head(10)
print(high_intent.to_string())

# ── PLATFORM-LEVEL INSIGHT (CORE BUSINESS ANSWER) ────────────────────────────
print("\n=== Platform Intent Rate (THE KEY FINDING) ===")
platform_summary = df.groupby("platform").agg(
    total_posts=("intent_tier", "count"),
    high_intent=("intent_tier", lambda x: (x == "High Intent").sum()),
    medium_intent=("intent_tier", lambda x: (x == "Medium Intent").sum()),
).reset_index()

platform_summary["high_intent_rate_%"] = (
    platform_summary["high_intent"] / platform_summary["total_posts"] * 100
).round(2)

print(platform_summary.to_string(index=False))

# ── SAVE ──────────────────────────────────────────────────────────────────────
os.makedirs("data/processed", exist_ok=True)
output_path = "data/processed/intent_classified.csv"
df.to_csv(output_path, index=False)
print(f"\n✓ Saved to {output_path}")
print(f"✓ {len(df)} posts classified")
