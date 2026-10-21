"""Altair chart builders for the dashboard.

Colour rules: brands use fixed categorical slots (validated for colour-vision
deficiency); ordered steps use one blue ramp; text always uses ink colours,
never series colours. Every chart has a tooltip and a table nearby.
"""

import altair as alt
import pandas as pd

from fashion_intel.metrics import COMPOSITION_ORDER

INK = "#2f2e2b"
INK_MUTED = "#6b6a65"
GRID = "#e6e4dd"
BRAND_SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
FUNNEL_RAMP = ["#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#86b6ef"]
COMPOSITION_COLORS = ["#184f95", "#3987e5", "#eda100", "#1baf7a", "#b4b2a9", "#dcdad3"]
SCOPE_COLORS = {"Audit window (60 days)": "#2a78d6", "All collected posts": "#eb6834"}


def brand_scale(display_names: list[str]) -> alt.Scale:
    return alt.Scale(domain=display_names, range=BRAND_SLOTS[: len(display_names)])


def _style(chart: alt.Chart, height: int) -> alt.Chart:
    return chart.properties(height=height).configure_view(strokeWidth=0).configure_axis(
        gridColor=GRID, domainColor=GRID, tickColor=GRID, labelColor=INK_MUTED, titleColor=INK_MUTED,
        labelFontSize=12, titleFontSize=12, titleFontWeight="normal",
    ).configure_legend(labelColor=INK, titleColor=INK_MUTED, labelFontSize=12, orient="top")


def funnel(df: pd.DataFrame) -> alt.Chart:
    d = df.copy()
    d["label"] = [f"{int(c):,}  ({p:.1f}%)" if pd.notna(c) else "not observable in public data"
                  for c, p in zip(d["count"], d["pct_of_sampled"])]
    d["bar"] = d["count"].fillna(0)
    y = alt.Y("step:N", sort=d.sort_values("order")["step"].tolist(), title=None, axis=alt.Axis(labelLimit=260))
    bars = alt.Chart(d).mark_bar(cornerRadiusEnd=4, height=22).encode(
        y=y, x=alt.X("bar:Q", title="Comments", axis=alt.Axis(format="d", tickMinStep=1),
                  scale=alt.Scale(domainMax=float(d["bar"].max()) * 1.35 or 1)),
        color=alt.Color("step:N", scale=alt.Scale(domain=d["step"].tolist(), range=FUNNEL_RAMP), legend=None),
        tooltip=[alt.Tooltip("step:N", title="Step"), alt.Tooltip("label:N", title="Count")])
    text = alt.Chart(d).mark_text(align="left", dx=6, color=INK, fontSize=12).encode(y=y, x="bar:Q", text="label:N")
    return _style(bars + text, 230)


def composition(df: pd.DataFrame, group: str = "brand") -> alt.Chart:
    d = df.assign(cat_order=df["category"].map(COMPOSITION_ORDER.index))
    order = d.drop_duplicates(group).sort_values("group_total", ascending=False)[group].tolist()
    return _style(alt.Chart(d).mark_bar(height=26, stroke="white", strokeWidth=1.5).encode(
        y=alt.Y(f"{group}:N", title=None, sort=order),
        x=alt.X("share_pct:Q", stack="normalize", title="Share of sampled audience comments",
                axis=alt.Axis(format="%")),
        color=alt.Color("category:N", title=None, scale=alt.Scale(domain=COMPOSITION_ORDER, range=COMPOSITION_COLORS),
                        legend=alt.Legend(columns=2, symbolType="square", labelLimit=0)),
        order=alt.Order("cat_order:Q"),
        tooltip=[alt.Tooltip(f"{group}:N", title="Brand"), alt.Tooltip("category:N", title="Category"),
                 alt.Tooltip("comments:Q", title="Comments"), alt.Tooltip("share_pct:Q", title="Share %", format=".1f"),
                 alt.Tooltip("group_total:Q", title="Comments sampled")],
    ), alt.Step(44))


def scope_comparison(df: pd.DataFrame) -> alt.Chart:
    """High+medium rate per brand for two scopes, with 95% CI and value labels."""
    d = df.assign(label=df["high_or_medium_rate_pct"].map(lambda v: f"{v:.1f}%" if pd.notna(v) else "–"))
    x_max = max(10.0, float(d["high_or_medium_rate_pct"].max() or 0) * 1.6)
    d["hm_ci_high_shown"] = d["hm_ci_high"].clip(upper=x_max)
    base = alt.Chart(d).encode(
        y=alt.Y("brand:N", title=None),
        yOffset=alt.YOffset("scope:N", sort=list(SCOPE_COLORS)),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, height=14).encode(
        x=alt.X("high_or_medium_rate_pct:Q", title="Comments with a shopping signal (high + medium), %",
                scale=alt.Scale(domain=[0, x_max], clamp=True)),
        color=alt.Color("scope:N", title=None, scale=alt.Scale(domain=list(SCOPE_COLORS), range=list(SCOPE_COLORS.values()))),
        tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("scope:N", title="Scope"),
                 alt.Tooltip("sampled_comments:Q", title="Comments sampled"), alt.Tooltip("high:Q", title="High"),
                 alt.Tooltip("medium:Q", title="Medium"), alt.Tooltip("label:N", title="Rate"),
                 alt.Tooltip("hm_ci_low:Q", title="95% CI low"), alt.Tooltip("hm_ci_high:Q", title="95% CI high")])
    ci = base.mark_rule(strokeWidth=1.5, color=INK_MUTED, opacity=0.6).encode(x="hm_ci_low:Q", x2="hm_ci_high_shown:Q")
    text = base.mark_text(align="left", dx=5, color=INK, fontSize=11).encode(x="high_or_medium_rate_pct:Q", text="label:N")
    return _style(ci + bars + text, 80 + 64 * d["brand"].nunique())


def coverage_timeline(posts: pd.DataFrame, window: dict, scale: alt.Scale) -> alt.Chart:
    d = posts.dropna(subset=["published_at_utc"]).copy()
    d["date"] = d["published_at_utc"].dt.tz_convert(None)
    d["post kind"] = d.apply(lambda r: "Pinned" if r["is_pinned"] else ("Collab (partner-owned)" if r["is_collab"] else "Own post"), axis=1)
    band = pd.DataFrame({"start": [pd.Timestamp(window["start_utc"]).tz_convert(None)],
                         "end": [pd.Timestamp(window["end_utc"]).tz_convert(None)], "label": ["60-day audit window"]})
    rect = alt.Chart(band).mark_rect(color="#2a78d6", opacity=0.10).encode(x="start:T", x2="end:T")
    rect_label = alt.Chart(band).mark_text(align="right", baseline="top", dx=-4, dy=-14, color="#256abf", fontSize=11).encode(
        x="end:T", y=alt.value(0), text="label:N")
    dots = alt.Chart(d).mark_point(size=80, filled=True, opacity=0.9, strokeWidth=1.5).encode(
        x=alt.X("date:T", title="Post published", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("brand:N", title=None),
        color=alt.Color("brand:N", scale=scale, legend=None),
        shape=alt.Shape("post kind:N", title=None, scale=alt.Scale(domain=["Own post", "Collab (partner-owned)", "Pinned"],
                                                                   range=["circle", "triangle-up", "diamond"])),
        tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("published_date_wat:N", title="Date"),
                 alt.Tooltip("post kind:N", title="Kind"), alt.Tooltip("post_type:N", title="Format"),
                 alt.Tooltip("in_audit_window:N", title="In window")])
    return _style(rect + rect_label + dots, 70 + 44 * d["brand"].nunique())


def seller_signals(df: pd.DataFrame) -> alt.Chart:
    d = df.melt(id_vars=["brand", "posts"], value_vars=["shows_price_pct", "call_to_action_pct", "launch_or_restock_pct"],
                var_name="signal", value_name="pct")
    names = {"shows_price_pct": "Shows a ₦ price", "call_to_action_pct": "Call to action (shop / DM / link)",
             "launch_or_restock_pct": "Launch or restock"}
    d["signal"] = d["signal"].map(names)
    d["label"] = d["pct"].map(lambda v: f"{v:.0f}%")
    base = alt.Chart(d).encode(y=alt.Y("brand:N", title=None), yOffset=alt.YOffset("signal:N", sort=list(names.values())))
    bars = base.mark_bar(cornerRadiusEnd=4, height=10).encode(
        x=alt.X("pct:Q", title="Share of the brand's captions (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("signal:N", title=None, scale=alt.Scale(domain=list(names.values()), range=BRAND_SLOTS[:3]),
                        legend=alt.Legend(labelLimit=0)),
        tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("signal:N", title="Caption signal"),
                 alt.Tooltip("label:N", title="Share of captions"), alt.Tooltip("posts:Q", title="Posts")])
    text = base.transform_filter("datum.pct > 0").mark_text(align="left", dx=4, color=INK, fontSize=11).encode(x="pct:Q", text="label:N")
    return _style(bars + text, 80 + 58 * d["brand"].nunique())


def interactions_strip(posts: pd.DataFrame, scale: alt.Scale) -> alt.Chart:
    d = posts.dropna(subset=["interactions"]).assign(interactions=lambda x: x["interactions"].astype(float))
    dots = alt.Chart(d).mark_circle(size=90, opacity=0.85, stroke="white", strokeWidth=2).encode(
        x=alt.X("interactions:Q", scale=alt.Scale(type="log"), title="Interactions per post (likes + comments, log scale)"),
        y=alt.Y("brand:N", title=None), color=alt.Color("brand:N", scale=scale, legend=None),
        tooltip=[alt.Tooltip("brand:N", title="Brand"), alt.Tooltip("published_date_wat:N", title="Date"),
                 alt.Tooltip("post_type:N", title="Format"), alt.Tooltip("likes:Q", title="Likes", format=","),
                 alt.Tooltip("comments_count:Q", title="Comments", format=","), alt.Tooltip("is_collab:N", title="Collab")])
    med = d.groupby("brand", as_index=False)["interactions"].median()
    ticks = alt.Chart(med).mark_tick(thickness=2, size=26, color=INK).encode(
        x="interactions:Q", y="brand:N", tooltip=[alt.Tooltip("brand:N"), alt.Tooltip("interactions:Q", title="Median", format=",.0f")])
    return _style(dots + ticks, 60 + 44 * d["brand"].nunique())


def format_mix(df: pd.DataFrame, scale: alt.Scale) -> alt.Chart:
    names = {"clips": "Reel", "Sidecar": "Carousel", "Image": "Image", "Video": "Video"}
    d = df.assign(format=df["post_type"].map(lambda v: names.get(v, str(v))))
    return _style(alt.Chart(d).mark_point(size=150, filled=True, opacity=0.95, stroke="white", strokeWidth=1.5).encode(
        y=alt.Y("brand:N", title=None),
        x=alt.X("median_interactions:Q", scale=alt.Scale(type="log"), title="Median interactions per post (log scale)"),
        shape=alt.Shape("format:N", title=None, scale=alt.Scale(domain=["Reel", "Carousel", "Image"],
                                                                range=["circle", "square", "triangle-up"])),
        color=alt.Color("format:N", title=None, scale=alt.Scale(domain=["Reel", "Carousel", "Image"], range=BRAND_SLOTS[:3])),
        tooltip=[alt.Tooltip("brand:N"), alt.Tooltip("format:N"), alt.Tooltip("posts:Q", title="Posts"),
                 alt.Tooltip("median_interactions:Q", title="Median interactions", format=",.0f")]),
        alt.Step(40))


def weekly_volume(posts: pd.DataFrame, scale: alt.Scale) -> alt.Chart:
    w = posts.dropna(subset=["published_at_utc"]).assign(
        week=lambda d: pd.to_datetime(d["published_date_wat"]).dt.to_period("W-SUN").dt.start_time)
    w = w.groupby(["week", "brand"]).size().rename("posts").reset_index()
    w["week_label"] = w["week"].dt.strftime("%d %b %Y")
    order = w.sort_values("week")["week_label"].unique().tolist()
    return _style(alt.Chart(w).mark_bar(stroke="white", strokeWidth=1.5, cornerRadiusEnd=2).encode(
        x=alt.X("week_label:O", sort=order, title="Week starting (Lagos time)", axis=alt.Axis(labelAngle=-40)),
        y=alt.Y("posts:Q", title="Posts", axis=alt.Axis(tickMinStep=1)),
        color=alt.Color("brand:N", scale=scale, title=None, legend=alt.Legend(values=sorted(w["brand"].unique()))),
        tooltip=[alt.Tooltip("week_label:N", title="Week of"), alt.Tooltip("brand:N"), alt.Tooltip("posts:Q")]), 260)


def posting_heatmap(posts: pd.DataFrame, weekdays: list[str]) -> alt.Chart:
    h = posts.dropna(subset=["published_hour_wat"]).groupby(["published_weekday_wat", "published_hour_wat"]).size() \
        .rename("posts").reset_index()
    return _style(alt.Chart(h).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("published_hour_wat:O", title="Hour of day (WAT)"),
        y=alt.Y("published_weekday_wat:N", sort=weekdays, title=None, axis=alt.Axis(labelOverlap=False)),
        color=alt.Color("posts:Q", title="Posts", scale=alt.Scale(range=["#cde2fb", "#184f95"]),
                        legend=alt.Legend(orient="right", gradientLength=120)),
        tooltip=[alt.Tooltip("published_weekday_wat:N", title="Day"), alt.Tooltip("published_hour_wat:O", title="Hour"),
                 alt.Tooltip("posts:Q")]), alt.Step(30))


def weekday_performance(df: pd.DataFrame, weekdays: list[str]) -> alt.Chart:
    base = alt.Chart(df).encode(x=alt.X("published_weekday_wat:N", sort=weekdays, title=None,
                                        axis=alt.Axis(labelAngle=0, labelExpr="slice(datum.label, 0, 3)")))
    bars = base.mark_bar(cornerRadiusEnd=4, color="#2a78d6", width=28).encode(
        y=alt.Y("median_relative_performance:Q", title="Relative performance (1.0 = typical)"),
        tooltip=[alt.Tooltip("published_weekday_wat:N", title="Day"), alt.Tooltip("posts:Q", title="Posts"),
                 alt.Tooltip("brands:Q", title="Brands"), alt.Tooltip("median_relative_performance:Q", title="Median ×")])
    n = base.mark_text(dy=-8, color=INK_MUTED, fontSize=11).encode(
        y="median_relative_performance:Q", text=alt.Text("posts:Q", format="d"))
    rule = alt.Chart(pd.DataFrame({"y": [1.0]})).mark_rule(strokeDash=[4, 4], color=INK_MUTED).encode(y="y:Q")
    return _style(bars + rule + n, 260)
