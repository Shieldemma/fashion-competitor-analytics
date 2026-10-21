import pytest

from fashion_intel.intent import LABELS, caption_signals, classify

REQUIRED = [
    ("How much is this dress?", "high"),
    ("Please, do you deliver to Ikot Ekpene?", "high"),
    ("I want to order this outfit.", "high"),
    ("This dress is beautiful.", "low"),
    ("I love it but cannot afford it.", "low"),
    ("I don't want to buy this.", "no_signal"),
    ("Where can I get this?", "high"),
    ("The delivery was terrible.", "no_signal"),
    ("", "no_signal"),
    ("😍🔥😍", "no_signal"),
]


@pytest.mark.parametrize("text, expected", REQUIRED)
def test_required_examples(text, expected):
    assert classify(text).label == expected


@pytest.mark.parametrize("text, expected", [
    # Nigerian English / Pidgin
    ("Wetin be the price?", "high"), ("How much be this one abeg", "high"), ("Price abeg", "high"),
    ("Una dey deliver to Abuja?", "high"), ("I wan buy am", "high"), ("Last price?", "high"),
    ("Hw much for the green one", "high"),
    # negation
    ("I no wan buy am", "no_signal"), ("Not buying this", "no_signal"), ("I will never buy from here again", "no_signal"),
    ("Don't you deliver to Enugu?", "high"),          # negated *question* is still an inquiry
    ("Can't wait to wear this", "medium"),           # "can't wait" is not a negation
    # word boundaries
    ("Nice costume", "low"), ("Our admin team is random", "no_signal"), ("Priceless 🔥", "low"),
    # ambiguity
    ("where?", "uncertain"), ("Maybe I'll get one later", "uncertain"), ("Hello can you check your dm", "uncertain"),
    ("Unable to send media via dm", "uncertain"),
    # post-purchase is not new intent
    ("I never received my order", "no_signal"),
])
def test_edge_cases(text, expected):
    assert classify(text).label == expected


def test_negation_is_flagged():
    r = classify("I don't want to buy this.")
    assert r.negated and "negated_purchase" in r.signals


def test_affordability_and_post_purchase_tags():
    assert "affordability_barrier" in classify("Too expensive for me but lovely").signals
    assert "post_purchase_feedback" in classify("The delivery was terrible.").signals


def test_repeated_signals_count_distinct_types():
    once = classify("How much?")
    many = classify("How much? How much? How much??")
    multi = classify("How much is it and do you deliver to Lagos?")
    assert once.signal_count == many.signal_count == 1
    assert multi.signal_count == 2


def test_compliment_is_not_purchase_intent():
    for text in ["Gorgeous queen", "Stunning as always", "This is fire 🔥", "I love this"]:
        assert classify(text).label not in {"high", "medium"}, text


@pytest.mark.parametrize("weird", [None, float("nan"), 123, "   ", "@someone", "https://x.com/abc", "!!!", "🙏🏿" * 50])
def test_never_raises_and_returns_valid_label(weird):
    assert classify(weird).label in LABELS


def test_caption_signals_are_seller_side():
    s = caption_signals("Price: ₦110,000. Shop online at www.zivalagos.com. New collection!")
    assert s == {"shows_price": True, "call_to_action": True, "launch_or_restock": True}
    assert caption_signals("") == {"shows_price": False, "call_to_action": False, "launch_or_restock": False}
