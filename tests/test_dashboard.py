"""Dashboard smoke test + agreement between dashboard KPIs and the pipeline's analysis tables."""
import pandas as pd
import pytest

from fashion_intel import metrics
from fashion_intel.config import ANALYSIS_DIR, PROCESSED_DIR
from fashion_intel.pipeline import load_processed

pytestmark = pytest.mark.skipif(not (PROCESSED_DIR / "posts.csv").exists(), reason="run the pipeline first")


def test_dashboard_kpis_match_analysis_tables():
    posts, comments, _ = load_processed()
    p, c = metrics.scope(posts, comments, window_only=True)
    k = metrics.kpis(p, c)
    by_brand = pd.read_csv(ANALYSIS_DIR / "intent_by_brand.csv")
    assert k["sampled_comments"] == by_brand["sampled_comments"].sum()
    assert k["high"] == by_brand["high"].sum()
    assert k["high_or_medium"] == by_brand["high_or_medium"].sum()
    by_platform = pd.read_csv(ANALYSIS_DIR / "intent_by_platform.csv")
    assert k["high_or_medium_rate_pct"] == pytest.approx(
        by_platform["high_or_medium"].sum() / by_platform["sampled_comments"].sum() * 100, abs=0.01)


def test_dashboard_renders_without_exceptions():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("dashboard/streamlit_app.py", default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Competitors with data" in m.label for m in at.metric)


def test_dashboard_empty_filter_shows_message_not_error():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("dashboard/streamlit_app.py", default_timeout=60).run()
    at.sidebar.multiselect[0].set_value([]).run()
    assert not at.exception
    assert any("No posts match" in w.value for w in at.warning)
