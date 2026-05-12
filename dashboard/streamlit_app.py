# dashboard/streamlit_app.py
# Run this with: streamlit run dashboard/streamlit_app.py
# Opens automatically in your browser at http://localhost:8501

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lagos Fashion Intelligence",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = "data/processed/intent_classified.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    # fallback: load from cleaned if processed not ready
    path2 = "data/cleaned/cleaned_posts.csv"
    if os.path.exists(path2):
        return pd.read_csv(path2)
    return None

df = load_data()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("Lagos Fashion Competitor Intelligence")
st.caption("Social media engagement & purchase-intent audit — Instagram")

if df is None:
    st.error("No data found. Run the scraper and cleaning pipeline first.")
    st.code("python scraper/instagram_scraper.py\npython analytics/clean_data.py\npython analytics/intent_classifier.py")
    st.stop()

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

brands = ["All brands"] + sorted(df["brand"].unique().tolist())
selected_brand = st.sidebar.selectbox("Filter by brand", brands)

if selected_brand != "All brands":
    df_view = df[df["brand"] == selected_brand]
else:
    df_view = df

# ── KPI METRICS ROW ───────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Brands tracked", df["brand"].nunique())

with col2:
    st.metric("Total posts", len(df_view))

with col3:
    high_intent = (df_view.get("intent_tier", pd.Series()) == "High Intent").sum()
    st.metric("High-intent posts", int(high_intent))

with col4:
    avg_eng = df_view["engagement_rate"].mean()
    st.metric("Avg engagement rate", f"{avg_eng:.2f}%")

with col5:
    top_brand = (
        df.groupby("brand")["engagement_rate"]
        .mean()
        .idxmax()
    )
    st.metric("Top brand", top_brand)

st.divider()

# ── CHART ROW 1 ───────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

BRAND_COLORS = {
    "veekeejames_official": "#E24B4A",
    "ashluxe":              "#1D9E75",
    "wflsncrm":             "#378ADD",
    "zivalagos":            "#BA7517",
    "yomicasual":           "#7F77DD",
}

with col_a:
    st.subheader("Engagement rate by brand")

    brand_eng = (
        df_view.groupby("brand")["engagement_rate"]
        .mean()
        .sort_values(ascending=True)
    )

    colors = [BRAND_COLORS.get(b, "#888780") for b in brand_eng.index]

    fig1, ax1 = plt.subplots(figsize=(6, 3))
    brand_eng.plot(kind="barh", ax=ax1, color=colors, edgecolor="none")
    ax1.set_xlabel("Average engagement rate (%)")
    ax1.set_ylabel("")
    ax1.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)

with col_b:
    st.subheader("Purchase intent by brand")

    if "intent_tier" in df_view.columns:
        intent_pivot = df_view.groupby(
            ["brand", "intent_tier"]
        ).size().unstack(fill_value=0)

        fig2, ax2 = plt.subplots(figsize=(6, 3))
        intent_colors = {
            "High Intent":   "#E24B4A",
            "Medium Intent": "#BA7517",
            "Low Intent":    "#B4B2A9",
            "No Signal":     "#D3D1C7"
        }
        col_colors = [intent_colors.get(c, "#888780") for c in intent_pivot.columns]
        intent_pivot.plot(
            kind="bar", ax=ax2, stacked=True,
            color=col_colors, edgecolor="none"
        )
        ax2.set_xlabel("")
        ax2.set_ylabel("Posts")
        ax2.tick_params(axis="x", rotation=30)
        ax2.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.info("Run intent_classifier.py first to see intent data")

# ── CHART ROW 2 ───────────────────────────────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Likes distribution by brand")

    fig3, ax3 = plt.subplots(figsize=(6, 3))
    brands_list = df_view["brand"].unique()
    data_to_plot = [
        df_view[df_view["brand"] == b]["likes"].values
        for b in brands_list
    ]
    bp = ax3.boxplot(data_to_plot, labels=brands_list, patch_artist=True)
    for patch, brand in zip(bp["boxes"], brands_list):
        patch.set_facecolor(BRAND_COLORS.get(brand, "#888780"))
        patch.set_alpha(0.7)
    ax3.tick_params(axis="x", rotation=30)
    ax3.set_ylabel("Likes per post")
    ax3.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)

with col_d:
    st.subheader("Sentiment distribution")

    if "sentiment" in df_view.columns:
        sentiment_counts = df_view["sentiment"].value_counts()
        sentiment_colors = ["#1D9E75", "#E24B4A", "#888780"]

        fig4, ax4 = plt.subplots(figsize=(5, 3))
        sentiment_counts.plot(
            kind="pie", ax=ax4,
            colors=sentiment_colors,
            autopct="%1.0f%%",
            startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 1}
        )
        ax4.set_ylabel("")
        ax4.set_title("")
        plt.tight_layout()
        st.pyplot(fig4)
    else:
        st.info("Sentiment data not available — run intent_classifier.py")

st.divider()

# ── RAW DATA TABLE ────────────────────────────────────────────────────────────
with st.expander("View raw data table"):
    st.dataframe(
        df_view[["brand", "likes", "engagement_rate",
                 "intent_tier", "caption"]].head(100),
        use_container_width=True
    )

# ── BUDGET RECOMMENDATION ─────────────────────────────────────────────────────
st.subheader("Budget allocation recommendation")

rec = pd.DataFrame({
    "Platform":         ["Instagram", "TikTok", "Facebook", "Twitter/X"],
    "Recommended %":    [50, 30, 15, 5],
    "Why":              [
        "Highest purchase-intent signals in Lagos fashion",
        "Highest reach, growing commerce behaviour",
        "Older audience demographic, lower conversion rate",
        "Minimal fashion purchase conversion signals"
    ]
})

st.dataframe(rec, use_container_width=True, hide_index=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.caption("Data collected via Playwright scraper. Engagement = likes / followers × 100. Intent = keyword NLP classifier.")
