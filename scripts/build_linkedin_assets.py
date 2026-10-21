# scripts/build_linkedin_assets.py
# Builds LinkedIn visuals from the pipeline outputs, so every number matches the dashboard.
#   python scripts/build_linkedin_assets.py
# Output: docs/linkedin/linkedin_carousel.pdf (6 slides, 1080x1350), slide PNGs, linkedin_summary.png
# Needs Google Chrome installed (rendered headless via Playwright: pip install -r requirements-scraper.txt).

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fashion_intel import metrics  # noqa: E402
from fashion_intel.config import load_brand_config  # noqa: E402
from fashion_intel.pipeline import load_processed  # noqa: E402

OUT = ROOT / "docs" / "linkedin"
REPO = "github.com/Shieldemma/fashion-competitor-analytics"
AUTHOR = "Otuekong Emmanuel"
BLUE, BLUE_D, ORANGE, AQUA, YELLOW = "#2a78d6", "#184f95", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, LINE, SOFT = "#1f2328", "#5b5f66", "#e4e2dc", "#f4f7fb"
COMP_COLORS = dict(zip(metrics.COMPOSITION_ORDER, ["#184f95", "#3987e5", YELLOW, AQUA, "#b4b2a9", "#dcdad3"]))


def esc(s) -> str:
    return html.escape(str(s))


# ── Data ────────────────────────────────────────────────────────────────────
posts_all, comments_all, manifest = load_processed()
cfg = load_brand_config()
display = {b["brand_handle"]: b["display_name"] for b in cfg["brands"]}
p_win, c_win = metrics.scope(posts_all, comments_all, window_only=True)
p_all, c_all = metrics.scope(posts_all, comments_all, window_only=False)
k_win, k_all = metrics.kpis(p_win, c_win), metrics.kpis(p_all, c_all)
funnel = metrics.intent_funnel(c_win)
comp = metrics.comment_composition(c_win, "brand_handle")
share = comp.groupby("category")["comments"].sum() / comp["comments"].sum() * 100
cap = metrics.caption_signal_summary(p_win).set_index("brand_handle")
top_price = cap["shows_price_pct"].idxmax()
cov = metrics.coverage_by_brand(posts_all, comments_all, cfg)
n_brands = int((cov["posts_collected"] > 0).sum())
emoji_pct = share.get("Emoji or tag only", 0)
praise_pct = share.get("Compliment / product interest", 0)
n_tests = 125
others_price_max = cap.drop(index=top_price)["shows_price_pct"].max()
top_name = display[top_price] + ("'" if display[top_price].endswith("s") else "'s")


# ── SVG charts ──────────────────────────────────────────────────────────────
def funnel_svg(width=920, row_h=74) -> str:
    rows = funnel.to_dict("records")
    n0 = rows[0]["count"] or 1
    label_w, bar_w = 400, width - 400 - 150
    parts = [f'<svg width="{width}" height="{row_h * len(rows)}" xmlns="http://www.w3.org/2000/svg">']
    ramp = ["#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#86b6ef"]
    for i, r in enumerate(rows):
        y = i * row_h
        c = r["count"]
        w = 0 if c is None or c != c else max(4, bar_w * c / n0)
        val = "not observable" if c is None or c != c else f"{int(c):,}"
        parts.append(f'<text x="{label_w - 16}" y="{y + 44}" text-anchor="end" font-size="24" fill="{INK}">{esc(r["step"].replace(" (not just emoji/tags)", ""))}</text>')
        if w:
            parts.append(f'<rect x="{label_w}" y="{y + 14}" width="{w}" height="{row_h - 30}" rx="6" fill="{ramp[i]}"/>')
        parts.append(f'<text x="{label_w + w + 14}" y="{y + 45}" font-size="27" font-weight="700" fill="{INK}">{val}</text>')
    parts.append("</svg>")
    return "".join(parts)


def composition_svg(width=920) -> str:
    order = comp.drop_duplicates("brand_handle").sort_values("group_total", ascending=False)["brand_handle"].tolist()
    label_w, bar_w, row_h = 200, width - 200 - 10, 70
    parts = [f'<svg width="{width}" height="{row_h * len(order) + 10}" xmlns="http://www.w3.org/2000/svg">']
    for i, b in enumerate(order):
        y = i * row_h
        g = comp[comp["brand_handle"] == b].set_index("category")
        parts.append(f'<text x="{label_w - 16}" y="{y + 42}" text-anchor="end" font-size="25" fill="{INK}">{esc(display.get(b, b))}</text>')
        x = label_w
        for cat in metrics.COMPOSITION_ORDER:
            if cat in g.index:
                w = bar_w * g.loc[cat, "share_pct"] / 100
                parts.append(f'<rect x="{x}" y="{y + 12}" width="{max(w - 3, 1)}" height="44" fill="{COMP_COLORS[cat]}"/>')
                x += w
    parts.append("</svg>")
    return "".join(parts)


def legend_html(cats) -> str:
    return "".join(f'<span class="lg"><i style="background:{COMP_COLORS[c]}"></i>{esc(c)}</span>' for c in cats)


# ── Slides ──────────────────────────────────────────────────────────────────
CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif; color: {INK}; background: #fff; }}
.slide {{ width: 1080px; height: 1350px; padding: 88px 80px 70px; position: relative; overflow: hidden;
          page-break-after: always; display: flex; flex-direction: column; background: #fff; }}
.kicker {{ font-size: 24px; letter-spacing: 3px; font-weight: 700; color: {BLUE}; text-transform: uppercase; }}
h1 {{ font-size: 70px; line-height: 1.08; font-weight: 800; margin-top: 28px; letter-spacing: -1px; }}
h2 {{ font-size: 54px; line-height: 1.12; font-weight: 800; margin-top: 22px; letter-spacing: -0.5px; }}
p.lead {{ font-size: 31px; line-height: 1.45; color: {MUTED}; margin-top: 26px; }}
.big {{ font-size: 200px; font-weight: 900; color: {BLUE_D}; letter-spacing: -6px; line-height: 1; }}
.card {{ background: {SOFT}; border-radius: 22px; padding: 34px 38px; margin-top: 30px; }}
.card h3 {{ font-size: 30px; margin-bottom: 10px; }}
.card p {{ font-size: 27px; line-height: 1.45; color: {MUTED}; }}
.foot {{ position: absolute; left: 80px; right: 80px; bottom: 50px; display: flex; justify-content: space-between; gap: 20px;
         font-size: 22px; color: {MUTED}; border-top: 2px solid {LINE}; padding-top: 22px; }}
.pill {{ display: inline-block; background: #fff; border: 2px solid {LINE}; border-radius: 999px; padding: 10px 22px;
         font-size: 24px; margin: 0 12px 14px 0; font-weight: 600; }}
.flow {{ display: flex; flex-direction: column; gap: 16px; margin-top: 34px; }}
.step {{ display: flex; align-items: center; gap: 24px; background: {SOFT}; border-radius: 18px; padding: 22px 28px; }}
.step b {{ background: {BLUE}; color: #fff; border-radius: 50%; width: 52px; height: 52px; display: flex; align-items: center;
           justify-content: center; font-size: 26px; flex-shrink: 0; }}
.step div {{ font-size: 27px; line-height: 1.35; }} .step span {{ color: {MUTED}; }}
.lg {{ display: inline-flex; align-items: center; font-size: 22px; color: {MUTED}; margin: 0 22px 10px 0; }}
.lg i {{ width: 20px; height: 20px; border-radius: 4px; display: inline-block; margin-right: 8px; }}
.stat {{ display: flex; gap: 24px; margin-top: 30px; }}
.stat div {{ flex: 1; background: {SOFT}; border-radius: 20px; padding: 28px; }}
.stat strong {{ display: block; font-size: 64px; font-weight: 900; color: {BLUE_D}; letter-spacing: -1px; }}
.stat span {{ font-size: 24px; color: {MUTED}; line-height: 1.35; display: block; margin-top: 6px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 18px; font-size: 25px; }}
td {{ padding: 16px 12px; border-top: 2px solid {LINE}; vertical-align: top; line-height: 1.35; }}
td:first-child {{ font-weight: 800; color: {BLUE}; width: 110px; }}
.no {{ color: #d03b3b; font-weight: 800; }}
.arrow {{ font-size: 30px; color: {BLUE}; font-weight: 700; margin-top: auto; padding-bottom: 90px; }}
"""


def foot(i: int, total: int) -> str:
    return f'<div class="foot"><span>{AUTHOR} · Data analytics portfolio</span><span>{i} / {total}</span></div>'


def slides() -> list[str]:
    T = 6
    return [
        # 1 — hook
        f"""<section class="slide"><div class="kicker">Data analytics case study · Lagos fashion</div>
        <h1>Which social platform makes Lagos fashion customers buy?</h1>
        <p class="lead">I audited {n_brands} Lagos fashion brands' Instagram to find out. The answer surprised me.</p>
        <div style="margin-top:70px"><div class="big">{k_win['high']} of {k_win['sampled_comments']}</div>
        <p class="lead" style="margin-top:14px;color:{INK};font-weight:600">recent comments asked about price, ordering or delivery.</p></div>
        <div class="stat" style="margin-top:56px"><div><strong>{n_brands}</strong><span>competitor brands</span></div>
        <div><strong>{len(posts_all)}</strong><span>posts scraped</span></div>
        <div><strong>{k_all['sampled_comments']}</strong><span>comments classified with NLP</span></div></div>
        <div class="arrow">Swipe → what the data could and couldn't answer</div>{foot(1, T)}</section>""",
        # 2 — brief + build
        f"""<section class="slide"><div class="kicker">The brief → what I built</div>
        <h2>“Audit 5 competitors across platforms to decide the ad budget.”</h2>
        <p class="lead" style="font-size:26px">Based on a real Upwork job. Instagram rate-limited my own scraper, so I collected the public data with Apify.</p>
        <div class="flow">
        <div class="step"><b>1</b><div>Scraping <span>· Playwright attempt + Apify export, {len(posts_all)} posts &amp; {k_all['sampled_comments']} comments</span></div></div>
        <div class="step"><b>2</b><div>Python ETL <span>· validation, deduplication, provenance hashes, UTC→Lagos time</span></div></div>
        <div class="step"><b>3</b><div>NLP intent classifier <span>· negation, word boundaries, Nigerian Pidgin (“Wetin be the price?”)</span></div></div>
        <div class="step"><b>4</b><div>SQL warehouse <span>· SQLite/PostgreSQL, idempotent loads, SQL ⇄ Python checks</span></div></div>
        <div class="step"><b>5</b><div>Streamlit dashboard + report <span>· {n_tests} automated tests</span></div></div>
        </div>{foot(2, T)}</section>""",
        # 3 — funnel
        f"""<section class="slide"><div class="kicker">Finding 1 · the purchase-intent funnel</div>
        <h2>Comments are for applause, not checkout.</h2>
        <p class="lead">Last 60 days of public comments on {n_brands} brands' posts:</p>
        <div style="margin-top:46px">{funnel_svg()}</div>
        <div class="card"><p>Buying conversations most likely move to <b style="color:{INK}">DMs and WhatsApp</b>, which public data can't see.
        Across <i>all</i> collected posts, only {k_all['high_or_medium']} of {k_all['sampled_comments']} comments
        ({k_all['high_or_medium_rate_pct']:.1f}%) showed any shopping signal.</p></div>{foot(3, T)}</section>""",
        # 4 — composition + seller behaviour
        f"""<section class="slide"><div class="kicker">Finding 2 · what audiences actually write</div>
        <h2>{emoji_pct:.0f}% emoji or tags only. {praise_pct:.0f}% compliments.</h2>
        <div style="margin-top:40px">{composition_svg()}</div>
        <div style="margin-top:14px">{legend_html([c for c in metrics.COMPOSITION_ORDER if c in share.index])}</div>
        <div class="stat"><div><strong>{cap.loc[top_price, 'shows_price_pct']:.0f}%</strong><span>of {esc(top_name)} captions show a ₦ price</span></div>
        <div><strong>{others_price_max:.0f}%</strong><span>is the highest share for any other brand: a clear difference in selling style</span></div></div>
        <p class="lead" style="font-size:25px">Seller behaviour differs a lot. Audience behaviour barely does: praise everywhere, buying questions almost nowhere.</p>
        {foot(4, T)}</section>""",
        # 5 — honest answer
        f"""<section class="slide"><div class="kicker">Finding 3 · the honest answer</div>
        <h2>“Which platform should get the budget?”</h2>
        <div class="card" style="margin-top:34px"><h3 class="no">Not answerable from this data.</h3>
        <p>Only Instagram could be collected. Any “50% Instagram / 30% TikTok” split would have been invented.
        My first version of this project did exactly that — auditing it was the most valuable part.</p></div>
        <h3 style="font-size:34px;margin-top:44px">What I recommended instead: a 6-week attribution test</h3>
        <table>
        <tr><td>Wk 1</td><td>Separate WhatsApp link, UTM-tagged link and discount code per platform</td></tr>
        <tr><td>Wk 2–5</td><td>Equal small spend on Instagram, TikTok, WhatsApp Status; A/B test prices in captions</td></tr>
        <tr><td>Wk 6</td><td>Set the budget split from <b>cost per order</b>, not likes</td></tr>
        </table>{foot(5, T)}</section>""",
        # 6 — skills + CTA
        f"""<section class="slide"><div class="kicker">What this project demonstrates</div>
        <h2>From messy scraped data to a decision a business can trust.</h2>
        <div style="margin-top:44px">
        {''.join(f'<span class="pill">{s}</span>' for s in ["Web scraping", "Python · pandas", "ETL & data quality", "NLP / text classification",
                 "SQL · PostgreSQL", "Statistics · confidence intervals", "Sensitivity analysis", "Streamlit · Altair", "pytest · 125 tests",
                 "Data storytelling"])}
        </div>
        <div class="stat"><div><strong>{len(posts_all)}</strong><span>posts processed with full provenance</span></div>
        <div><strong>{k_all['sampled_comments']}</strong><span>comments classified (5 intent levels)</span></div>
        <div><strong>{n_tests}</strong><span>automated tests passing</span></div></div>
        <div class="card"><h3>Code, dashboard &amp; technical audit</h3><p style="color:{BLUE};font-weight:700">{REPO}</p></div>
        {foot(6, T)}</section>""",
    ]


def summary_page() -> str:
    """Single 1080x1350 image for a one-picture post."""
    return f"""<section class="slide"><div class="kicker">Data analytics case study · Lagos fashion</div>
    <h2 style="font-size:58px">Which social platform makes Lagos fashion customers buy?</h2>
    <div class="stat" style="margin-top:36px">
      <div><strong>{k_win['high']} / {k_win['sampled_comments']}</strong><span>recent comments asked to buy</span></div>
      <div><strong>{emoji_pct + praise_pct:.0f}%</strong><span>were emoji or compliments</span></div>
      <div><strong>{cap.loc[top_price, 'shows_price_pct']:.0f}%</strong><span>of {esc(top_name)} captions show a price</span></div></div>
    <div style="margin-top:30px">{funnel_svg(900, row_h=60)}</div>
    <div class="card" style="margin-top:20px"><h3>The honest answer</h3><p>The platform budget question can't be answered with Instagram-only data —
      so I recommended a 6-week attribution test measuring <b style="color:{INK}">cost per order</b>, not likes.</p></div>
    <div class="foot"><span>{AUTHOR} · Python ETL · NLP (incl. Pidgin) · SQL · Streamlit · {n_tests} tests</span><span style="color:{BLUE};font-weight:700">{REPO}</span></div>
    </section>"""


def page(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def main() -> None:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    s = slides()
    (OUT / "carousel.html").write_text(page("".join(s)), encoding="utf-8")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        pg = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for i, slide in enumerate(s, 1):
            pg.set_content(page(slide))
            pg.screenshot(path=str(OUT / f"slide_{i}.png"))
        pg.set_content(page(summary_page()))
        pg.screenshot(path=str(OUT / "linkedin_summary.png"))
        pg.set_content(page("".join(s)))
        pg.pdf(path=str(OUT / "linkedin_carousel.pdf"), width="1080px", height="1350px", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        browser.close()
    print(f"Wrote {len(s)} slides, carousel PDF and summary image to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
