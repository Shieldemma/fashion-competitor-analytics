from fashion_intel import sentiment
from fashion_intel.intent import classify


def test_basic_labels():
    assert sentiment.label(sentiment.polarity("This dress is beautiful")) == "positive"
    assert sentiment.label(sentiment.polarity("The delivery was terrible")) == "negative"
    assert sentiment.label(sentiment.polarity("Tour dates")) == "neutral"


def test_empty_is_none_not_neutral():
    assert sentiment.polarity("") is None
    assert sentiment.polarity(None) is None
    assert sentiment.label(None) == "none"


def test_emoji_only_is_scored():
    assert sentiment.label(sentiment.polarity("😍🔥🔥")) == "positive"
    assert sentiment.label(sentiment.polarity("😡👎")) == "negative"
    assert sentiment.label(sentiment.polarity("🇳🇬")) == "neutral"


def test_sentiment_and_intent_are_independent():
    # positive sentiment, no purchase intent
    assert sentiment.label(sentiment.polarity("Gorgeous!!! 😍")) == "positive"
    assert classify("Gorgeous!!! 😍").label == "low"
    # negative sentiment, still a purchase inquiry
    text = "How much is it? The last one I bought was terrible"
    assert sentiment.label(sentiment.polarity(text)) == "negative"
    assert classify(text).label == "high"
