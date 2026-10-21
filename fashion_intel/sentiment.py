"""Sentiment, kept separate from purchase intent.

Positive sentiment is not purchase intent ("This is gorgeous" buys nothing),
and negative sentiment is not the absence of it ("Price is too high, any
discount?" is a buyer). The two are stored and reported as separate columns.

Method: TextBlob polarity on the words, plus a small emoji lexicon because
TextBlob ignores emojis and most comments here are emoji reactions.
This is a heuristic, English-centred baseline. It does not understand
Pidgin, sarcasm, or slang compliments such as "this is mad".
"""

from __future__ import annotations

import re

from .clean import clean_text

POSITIVE_EMOJI = set("😍🔥❤💕💖💯👏🙌🥰😘🤩✨💜💚💙🖤🤍💛🧡😊😁😀🙏👌👍🏆⭐🌟💪🥂💗💓🫶😻👑💎")
NEGATIVE_EMOJI = set("😡😠👎💔🤮😒🙄😤🤬😞😔")
THRESHOLD = 0.1

try:
    from textblob import TextBlob
except ImportError:  # keep the pipeline runnable; emoji lexicon still works
    TextBlob = None


def polarity(text) -> float | None:
    """Return polarity in [-1, 1], or None when there is nothing to score."""
    t = clean_text(text)
    if not t:
        return None
    words = re.sub(r"[^A-Za-z' ]+", " ", t).strip()
    text_score = TextBlob(words).sentiment.polarity if (TextBlob and words) else 0.0
    pos = sum(ch in POSITIVE_EMOJI for ch in t)
    neg = sum(ch in NEGATIVE_EMOJI for ch in t)
    emoji_score = (pos - neg) / (pos + neg) if (pos + neg) else 0.0
    if text_score != 0.0 and emoji_score != 0.0:
        return round((text_score + emoji_score) / 2, 4)
    return round(text_score or emoji_score, 4)


def label(score: float | None) -> str:
    if score is None:
        return "none"
    if score > THRESHOLD:
        return "positive"
    if score < -THRESHOLD:
        return "negative"
    return "neutral"
