import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BRAND_CFG = {
    "audit_window_days": 60,
    "brands": [
        {"brand_handle": "alpha", "display_name": "Alpha", "platform": "instagram", "follower_count": 10000,
         "follower_source": "test", "follower_as_of": None},
        {"brand_handle": "beta", "display_name": "Beta", "platform": "instagram", "follower_count": None,
         "follower_source": "test", "follower_as_of": None},
        {"brand_handle": "gamma", "display_name": "Gamma", "platform": "instagram", "follower_count": 5000,
         "follower_source": "test", "follower_as_of": None},
    ],
}


def _post(input_handle, code, owner, ts, likes, comments, caption="", pinned="false", **extra):
    row = {
        "inputUrl": f"https://www.instagram.com/{input_handle}/ ",
        "url": f"https://www.instagram.com/p/{code}/",
        "shortCode": code, "ownerUsername": owner, "caption": caption, "timestamp": ts,
        "likesCount": likes, "commentsCount": comments, "type": "Image", "productType": "",
        "videoViewCount": "", "videoPlayCount": "", "isPinned": pinned, "isCommentsDisabled": "false",
        "error": "", "errorDescription": "", "coauthorProducers/0/username": "",
    }
    for i in range(2):
        for f in ("id", "text", "ownerUsername", "timestamp", "likesCount"):
            row.setdefault(f"latestComments/{i}/{f}", "")
        for f in ("id", "text", "ownerUsername", "timestamp", "likesCount"):
            row.setdefault(f"latestComments/{i}/replies/0/{f}", "")
    row.update(extra)
    return row


def _comment(i, cid, text, user, ts="2026-05-01T10:00:00.000Z", reply=False):
    prefix = f"latestComments/{i}/replies/0" if reply else f"latestComments/{i}"
    return {f"{prefix}/id": cid, f"{prefix}/text": text, f"{prefix}/ownerUsername": user,
            f"{prefix}/timestamp": ts, f"{prefix}/likesCount": "0"}


@pytest.fixture
def brand_cfg():
    return BRAND_CFG


@pytest.fixture
def apify_csv(tmp_path):
    rows = [
        _post("alpha", "A1", "alpha", "2026-05-01T12:00:00.000Z", "100", "10", "New drop! Price: ₦50,000. Shop now",
              **_comment(0, "c1", "How much is this?", "fan_one"),
              **_comment(1, "c2", "Gorgeous 😍", "fan_two"),
              **_comment(0, "c3", "Check your DM", "alpha", reply=True)),
        _post("alpha", "A2", "alpha", "2026-04-20T23:30:00.000Z", "-1", "5", "",
              **_comment(0, "c4", "I don't want to buy this", "fan_three")),
        # exact duplicate of A1 (re-scrape) -> must be deduplicated
        _post("alpha", "A1", "alpha", "2026-05-01T12:00:00.000Z", "100", "10", "New drop! Price: ₦50,000. Shop now",
              **_comment(0, "c1", "How much is this?", "fan_one")),
        # collab post owned by someone else, shown on beta's grid
        _post("beta", "B1", "partner_account", "2026-05-02T08:00:00.000Z", "1.2K", "40", "Collab",
              **_comment(0, "c5", "Do you deliver to Uyo?", "fan_four")),
        # old pinned post, outside the 60-day window
        _post("beta", "B2", "beta", "2025-01-01T08:00:00.000Z", "500", "2", "Pinned classic", pinned="true",
              **_comment(0, "c6", "Where can I get this?", "fan_five")),
        # malformed timestamp
        _post("beta", "B3", "beta", "not-a-date", "50", "1", "Mystery"),
        # scraper error row for gamma
        {**_post("gamma", "", "", "", "", "", ""), "url": "", "shortCode": "", "error": "no_items",
         "errorDescription": "Empty or private data for provided input"},
    ]
    df = pd.DataFrame(rows)
    path = tmp_path / "apify_test.csv"
    df.to_csv(path, index=False)
    return path
