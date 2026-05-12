import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

brands = {
    "veekeejames_official": 2000000,
    "ashluxe": 150000,
    "wflsncrm": 25000,
    "zivalagos": 80000,
    "yomicasual": 500000,
}

instagram_captions = [
    "New collection just dropped! DM to order. Available in all sizes.",
    "Price? Check our bio link for the full catalogue.",
    "Do you deliver to Abuja? Yes we do! Inbox us.",
    "Beautiful work on this piece. How much is this outfit?",
    "Stunning as always. Available in plus sizes?",
    "This is everything. Where can I order from?",
    "Can I get this in red? DM us your size and colour.",
    "New arrivals every Friday. Shop the link in bio.",
    "How to order: send us a DM with your size and location.",
    "Free delivery in Lagos this weekend only.",
    "The craftsmanship on this is insane. Price please!",
    "Do you ship to the UK? Yes! DM for international rates.",
    "Whatsapp us to place your order today.",
    "Restock alert — the sold out styles are back!",
    "Behind the scenes at our Lagos studio. Love this process.",
    "Made for the bold. New drop available now.",
    "Thank you for 500K followers. You are everything to us.",
    "Celebrity spotted wearing our latest collection.",
    "Custom orders available. Send us your measurements via DM.",
    "This fabric is fire. What colour should we restock first?",
    "Limited pieces available. Order before it sells out.",
    "Lagos Fashion Week ready. Swipe to see the full look.",
    "Payment via bank transfer or card. DM to get started.",
    "Available in sizes XS to 3XL. Inclusive fashion always.",
    "The comments section is everything. You guys are amazing.",
    "New editorial just shot. Full campaign drops Friday.",
    "How much for the full set? DM us for a price list.",
    "This sold out in 2 hours last time. Stock up now.",
    "Handmade in Lagos with love. Every piece is unique.",
    "We deliver nationwide. Order today, receive in 3 days.",
]

tiktok_captions = [
    "POV: You just discovered the best Lagos fashion brand.",
    "New drop alert. Link in bio to shop.",
    "This look took 3 hours to make. Worth it?",
    "Lagos street style is on another level fr.",
    "Outfit of the week. DM for price and availability.",
    "Behind the scenes of our latest shoot.",
    "Trending in Lagos right now. Do you have yours?",
    "The fit check you needed today.",
    "How much? Check the link in our bio!",
    "Viral fashion moment. Available in store now.",
]

posts = []

for brand, followers in brands.items():
    num_posts = random.randint(18, 25)
    for i in range(num_posts):
        platform = random.choice(["instagram", "instagram", "tiktok"])
        caption_pool = instagram_captions if platform == "instagram" else tiktok_captions
        caption = random.choice(caption_pool)

        if followers > 500000:
            base_likes = random.randint(8000, 45000)
        elif followers > 100000:
            base_likes = random.randint(2000, 12000)
        elif followers > 50000:
            base_likes = random.randint(800, 5000)
        else:
            base_likes = random.randint(200, 2000)

        likes = int(base_likes * random.uniform(0.6, 1.4))

        days_ago = random.randint(1, 60)
        hour = random.choice([7,8,9,12,13,17,18,19,20,21,22])
        post_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0,5))
        post_date = post_date.replace(hour=hour)

        posts.append({
            "brand": brand,
            "platform": platform,
            "post_url": f"https://www.instagram.com/p/sample_{brand}_{i}/",
            "caption": caption,
            "likes": likes,
            "followers": followers,
            "post_date": post_date.isoformat(),
        })

df = pd.DataFrame(posts)
print(f"Generated {len(df)} posts")
print(df[["brand", "platform", "likes", "caption"]].head(10).to_string())
print("\nBrand breakdown:")
print(df.groupby("brand")["likes"].agg(["count","mean"]).round(0))

df.to_csv("data/raw/instagram_posts.csv", index=False)
print("\n✓ Saved to data/raw/instagram_posts.csv")