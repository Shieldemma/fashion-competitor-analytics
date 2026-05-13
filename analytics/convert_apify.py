import pandas as pd
import os

print("Converting Apify data...\n")

df = pd.read_csv("data/raw/apify_raw.csv")
print(f"Raw Apify rows: {len(df)}")
print(f"Brands found: {df['ownerUsername'].unique()}")

FOLLOWERS = {
    "veekeejames_official": 2000000,
    "ashluxe": 150000,
    "wflsncrm": 25000,
    "zivalagos": 77000,
    "yomicasual": 1000000,
}

posts = []
for _, row in df.iterrows():
    brand = str(row.get("ownerUsername", "")).strip()
    followers = FOLLOWERS.get(brand, 100000)
    likes_raw = row.get("likesCount", 0)
    try:
        likes = int(float(likes_raw)) if pd.notna(likes_raw) else 0
    except:
        likes = 0
    comments_raw = row.get("commentsCount", 0)
    try:
        comments_count = int(float(comments_raw)) if pd.notna(comments_raw) else 0
    except:
        comments_count = 0
    posts.append({
        "brand": brand,
        "platform": "instagram",
        "post_url": row.get("url", ""),
        "caption": str(row.get("caption", "")).strip(),
        "likes": likes,
        "comments_count": comments_count,
        "followers": followers,
        "post_date": row.get("timestamp", ""),
        "first_comment": str(row.get("firstComment", "")),
        "post_type": str(row.get("type", "")),
    })

posts_df = pd.DataFrame(posts)
print(f"\nExtracted {len(posts_df)} posts")
print(posts_df[["brand","caption","likes","comments_count"]].head(10).to_string())

comments = []
comment_cols = [c for c in df.columns if c.startswith("latestComments/") and c.endswith("/text")]
for _, row in df.iterrows():
    brand = str(row.get("ownerUsername", "")).strip()
    post_url = row.get("url", "")
    for col in comment_cols:
        text = row.get(col, "")
        if pd.notna(text) and str(text).strip() not in ["", "nan"]:
            idx = col.split("/")[1]
            comments.append({
                "brand": brand,
                "post_url": post_url,
                "comment_text": str(text).strip(),
                "commenter_username": row.get(f"latestComments/{idx}/ownerUsername", ""),
                "comment_likes": row.get(f"latestComments/{idx}/likesCount", 0),
            })

comments_df = pd.DataFrame(comments)
print(f"\nExtracted {len(comments_df)} real comments")
print(comments_df[["brand","comment_text"]].head(15).to_string())

os.makedirs("data/raw", exist_ok=True)
posts_df.to_csv("data/raw/instagram_posts.csv", index=False)
comments_df.to_csv("data/raw/real_comments.csv", index=False)
print(f"\n✓ Saved {len(posts_df)} posts to data/raw/instagram_posts.csv")
print(f"✓ Saved {len(comments_df)} real comments to data/raw/real_comments.csv")
