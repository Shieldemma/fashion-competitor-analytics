"""Purchase-intent classification for audience comments (rule-based, transparent).

Labels (full definitions in docs/intent_taxonomy.md):

  high       Explicit request or question about price, ordering, availability,
             payment or delivery ("How much is this?", "Do you deliver to Uyo?").
  medium     Weaker shopping signal without a clear request: desire for the
             item ("I need this"), product-attribute questions, bare shopping
             words ("restock", "sizes").
  low        Product interest or compliment with no buying request
             ("This dress is beautiful"), including "love it but can't afford it".
  no_signal  Readable text with no purchase cue, explicitly negated purchase
             ("I don't want to buy this"), post-purchase feedback, or no text
             at all (empty, emoji-only, @mention-only).
  uncertain  A possible shopping cue whose meaning the rules cannot settle
             (bare "where?", "link?", hedged/hypothetical shopping talk).

Design notes
- Matching uses regex word boundaries, so "cost" does not fire on "costume"
  and "dm" does not fire on "admin".
- A purchase cue preceded by a negation ("don't", "never", Pidgin "no wan")
  is cancelled unless the sentence is a question ("Don't you deliver to PH?").
- Sentiment is NOT used here. See sentiment.py.
- A label describes the *text*, not the person: a "high" comment is a
  purchase-intent signal, not proof that anyone bought anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .clean import clean_text

LABELS = ("high", "medium", "low", "no_signal", "uncertain")
INTENT_RANK = {"high": 4, "medium": 3, "uncertain": 2, "low": 1, "no_signal": 0}


@dataclass(frozen=True)
class IntentResult:
    label: str
    signals: tuple[str, ...]
    reason: str
    negated: bool = False

    @property
    def signal_count(self) -> int:
        """Number of distinct purchase-signal types (high + medium cues)."""
        return sum(1 for s in self.signals if s in HIGH_PATTERNS or s in MEDIUM_PATTERNS)


# ── Text normalisation ──────────────────────────────────────────────────────

_SPELLING = [
    (r"\b(pls|plz|plss|plis|pliz|plsss)\b", "please"),
    (r"\bhw\b", "how"),
    (r"\b(wat|wht|wetin)\b", "what"),
    (r"\b(u)\b", "you"),
    (r"\b(ur)\b", "your"),
    (r"\b(dis)\b", "this"),
    (r"(?<!['\w])d\b", "the"),
    (r"\b(dont)\b", "don't"),
    (r"\b(cant)\b", "can't"),
    (r"\b(wont)\b", "won't"),
    (r"\b(im)\b", "i'm"),
    (r"\b(dm'?d|dmed|dm-ed)\b", "dmd"),
    (r"\b(ammount)\b", "amount"),
    (r"\b(deliever|delivar)\b", "deliver"),
]
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE = re.compile(r"@[\w.]+")
_REPEAT_RE = re.compile(r"([a-z])\1{2,}")
_LETTER_RE = re.compile(r"[a-z]")


def normalize(text) -> str:
    t = clean_text(text).lower()
    t = _URL_RE.sub(" ", t)
    t = _MENTION_RE.sub(" ", t)
    t = _REPEAT_RE.sub(r"\1", t)  # "pleeeease" -> "please", "sooo" -> "so"
    for pattern, repl in _SPELLING:
        t = re.sub(pattern, repl, t)
    return re.sub(r"\s+", " ", t).strip()


# ── Patterns ────────────────────────────────────────────────────────────────
# Each entry: signal name -> list of regexes (applied to normalized text).

_ITEM = r"(this|these|it|one|that|am|them|the (dress|outfit|set|piece|top|bag|shoe|shoes|gown|look|fit))"

HIGH_PATTERNS: dict[str, list[str]] = {
    "price_inquiry": [
        r"\bhow much\b",
        r"\b(what|what's|whats) (is |be )?(the |your )?(price|cost|amount)\b",
        r"\b(send|drop|dm|share|tell)( me)? (the |your )?(price|price list|cost)\b",
        r"\blast price\b",
        r"^(price|prices|the price|price list)( please| abeg| biko| sis| ma| sir)?\??$",
        r"\bprice( please| abeg| biko| list)\b",
        r"\bprice\s*\?",
        r"\b(cost|costs|go for)\b[^?.!]*\?",
    ],
    "order_request": [
        r"\b(i|we) ('d|would|wan|wanna|want|need|will|'ll|go) (like )?(to )?(order|buy|purchase|book|cop|get (one|this|it|am|that))\b",
        r"\b(i'd|we'd|i'll|we'll|i'm going to|i am going to|gonna) (like to |love to )?(order|buy|purchase|book|cop|get one)\b",
        r"\b(can|could|may) (i|we) (order|buy|purchase|book|place an order|get (one|this|it|that))\b",
        r"\b(how|where) (do|can|will|should|to) (i |we )?(order|buy|purchase|book|place an order|get (one|this|it|am|that))\b",
        r"\bhow to (order|buy|purchase|book)\b",
        r"\b(make|let) (i|me) (order|buy|pay|book)\b",
        r"\bi fit (order|buy|get am|get this|get one)\b",
        r"\b(take|collect) my money\b",
        r"\b(added|adding) (it |this )?to (my )?cart\b",
        r"\b(dmd|inboxed|messaged you|sent (you )?(a )?(dm|message))\b",
        r"\bplace (an |my )?order\b",
    ],
    "availability_inquiry": [
        r"\bwhere (can|do|will|could) (i|we|one) (get|buy|find|order|purchase)\b",
        r"\b(is|are) (this|these|it|they|the \w+) (still )?(available|in stock|sold out)\b",
        r"\b(still )?available\s*\?",
        r"\b(do|does) (you|it|this|they) (have|come|has|sell)\b[^.!]*\b(size|sizes|colou?rs?|black|white|red|blue|green|pink|xl|xxl|small|medium|large|plus)\b",
        r"\b(available|come|comes) in (size|sizes|my size|plus size|xl|xxl|xs|small|medium|large|\d+)\b",
        r"\bwhen (will|are|is|do) (you|it|this|they|the \w+) (be )?(restock|back|available)",
        r"\b(e|it|is it) (still )?dey\b[^.!]*\?",
        r"\buna (get|dey sell|sell|have)\b",
    ],
    "delivery_inquiry": [
        r"\b(do|can|will|does) (you|they|una) (also )?(deliver|ship|send|dispatch|waybill)\b",
        r"\buna (dey )?(deliver|ship|waybill)\b",
        r"\b(deliver|delivery|ship|shipping|waybill|send) to\b[^.!]*\?",
        r"\b(delivery|shipping|waybill) (fee|cost|price|charge|time)\b",
        r"\bpay(ment)? on delivery\b",
    ],
    "payment_inquiry": [
        r"\b(account|acct|bank) (number|details|no|info)\b",
        r"\bsend (your )?(account|acct)\b",
        r"\bhow (do|can|will) (i|we) pay\b",
        r"\b(do you|can i) (accept|pay with|pay via|pay by|use) (transfer|card|crypto|paypal|bank transfer)\b",
        r"\bpayment (plan|options?|methods?|link)\b",
        r"\b(installment|instalment)s?\b",
    ],
}

MEDIUM_PATTERNS: dict[str, list[str]] = {
    "desire": [
        r"\b(i|we) (need|want|neeed|wan) " + _ITEM + r"\b",
        r"\b(need|want) (this|these|one)\b",
        r"\bmust (have|get|cop) (this|it|one)\b",
        r"\bmy (next |birthday |wedding |graduation |dream |owambe )+(outfit|dress|look|fit|gown)\b",
        r"\b(saving|save) (up )?for\b",
        r"\bstart saving\b",
        r"\bwish ?list\b",
        r"\bi will wear\b",
        r"\bcan't wait to (wear|order|buy|get)\b",
        r"\b(you|veekee|vj) (need to|should|must|have to|go|will) (make|do|design|sew) (my|me|our|for me)\b",
        r"\b(i'm|i am|am) wearing this\b",
    ],
    "product_question": [
        r"\b(what|which) (fabric|material|size|sizes|colou?r|colou?rs)\b",
        r"\bsize chart\b",
        r"\bother colou?rs\b",
    ],
    "shopping_term": [
        r"\b(order|orders|buy|purchase|restock|restocking|in stock|sold out|available|sizes|delivery|shipping|price|cost|website|online store)\b",
        r"₦\s?\d",
        r"\b\d+k\b",
    ],
}

AFFORDABILITY = [
    r"\b(can't|cannot|can not|couldn't|could not|no fit|never fit) afford\b",
    r"\btoo (expensive|costly|pricey)\b",
    r"\b(no money|i'm broke|am broke|i am broke|no funds|money no dey)\b",
    r"\bthis (one )?(na|is for) (rich|big) (people|man|men|girls?)\b",
]

POST_PURCHASE = [
    r"\b(never|didn't|did not|haven't|have not|still not) (receive|received|get|got|arrive|arrived|deliver|delivered)\b",
    r"\b(delivery|order|package|parcel|item|dress|outfit|shipping|customer service)\b[^.!?]*\b(was|is|came|arrived|has been)\b[^.!?]*\b(terrible|bad|late|poor|awful|horrible|damaged|wrong|disappointing|slow)\b",
    r"\b(refund|scam|scammed|fraud)\b",
    r"\b(received|got|collected) my (order|package|parcel|dress|outfit|item)\b",
    r"\bstill waiting for my\b",
]

COMPLIMENT = [
    r"\b(beautiful|beauty|gorgeous|stunning|lovely|love|loving|loved|nice|amazing|fire|wow|perfect|elegant|classy|"
    r"slay|slayed|slaying|queen|king|dope|cute|pretty|fine|masterpiece|phenomenal|iconic|obsessed|awesome|great|"
    r"excellent|magnificent|breathtaking|goals|drip|swag|stylish|wonderful|talented|creative|blessed|"
    r"exquisite|divine|clean|sharp|hard|mad|crazy|insane|best|art|artistry|legend|goat|superior|brilliant|cool|epic|"
    r"sweet|fresh|fly|goddess|perfection|classic|priceless|fan|sick|ate|gem|lit|vibes?|fabulous)\b",
    r"\b10/10\b",
    r"\bon point\b",
    r"\bthis is everything\b",
    r"\bchef'?s kiss\b",
    r"\b(that|this|the) (dress|outfit|set|piece|top|bag|gown|look|fit|shirt|collection|colou?r)\b(?=.*[😍🔥❤💕💖🥰🤩✨💜💚🖤🤍])",
]

CONTACT = re.compile(r"\b(dm|dms|inbox|your (contact|number|phone number|whatsapp)|whatsapp (number|line))\b")
HEDGE = r"\b(maybe|might|thinking (of|about)|considering|not sure|perhaps|if only)\b"
AMBIGUOUS_FRAGMENTS = {"location", "location?", "where", "where?", "link", "link?", "available", "which", "which?", "how", "how?", "dm", "size", "size?", "sizes"}

NEGATIONS = r"(don't|do not|didn't|did not|not|never|no|can't|cannot|can not|won't|will not|wouldn't|no wan|i no|nobody|neither)"
NEGATION_EXCEPTIONS = re.compile(r"\b(can't wait|cannot wait|can not wait|why not|no doubt|not only)\b")
QUESTION_START = re.compile(r"^(do|does|did|can|could|is|are|will|would|where|how|when|what|which|abeg|please|una)\b")

_COMPILED = {
    name: [re.compile(p) for p in pats]
    for name, pats in {**HIGH_PATTERNS, **MEDIUM_PATTERNS}.items()
}
_AFFORD = [re.compile(p) for p in AFFORDABILITY]
_POST = [re.compile(p) for p in POST_PURCHASE]
_COMPL = [re.compile(p) for p in COMPLIMENT]
_HEDGE = re.compile(HEDGE)
_NEG_BEFORE = re.compile(r"\b" + NEGATIONS + r"\b(?:\W+\w+){0,3}\W*$")


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _is_question(sentence: str) -> bool:
    return sentence.rstrip().endswith("?") or bool(QUESTION_START.match(sentence))


def _match(sentence: str, name: str) -> list[re.Match]:
    return [m for rx in _COMPILED[name] for m in rx.finditer(sentence)]


def _negated(sentence: str, match: re.Match) -> bool:
    prefix = sentence[: match.start()]
    scrubbed = NEGATION_EXCEPTIONS.sub(" ", prefix)
    # Negation inside the match itself, e.g. "i no wan buy"
    inside = NEGATION_EXCEPTIONS.sub(" ", match.group(0))
    return bool(_NEG_BEFORE.search(scrubbed)) or bool(re.search(r"\b" + NEGATIONS + r"\b", inside))


def classify(text) -> IntentResult:
    """Classify one comment. Never raises; any input becomes a label."""
    norm = normalize(text)
    if not norm or not _LETTER_RE.search(norm):
        raw = clean_text(text)
        reason = "empty" if not raw else ("mention_only" if _MENTION_RE.search(raw) else "no_text_emoji_or_symbols")
        return IntentResult("no_signal", (), reason)

    if norm.strip(" .!") in AMBIGUOUS_FRAGMENTS:
        return IntentResult("uncertain", ("ambiguous_fragment",), "bare shopping word with no context")

    signals: list[str] = []
    negated_any = False
    high_hits, medium_hits = set(), set()

    for sentence in _sentences(norm):
        question = _is_question(sentence)
        hedged_sentence = bool(_HEDGE.search(sentence)) and not question
        for name in HIGH_PATTERNS:
            for m in _match(sentence, name):
                if _negated(sentence, m) and not question:
                    negated_any = True
                elif hedged_sentence:
                    medium_hits.add(name)  # "Maybe I'll get one" -> resolved as hedged below
                else:
                    high_hits.add(name)
        for name in MEDIUM_PATTERNS:
            for m in _match(sentence, name):
                if _negated(sentence, m) and not question:
                    negated_any = True
                else:
                    medium_hits.add(name)

    afford = any(rx.search(norm) for rx in _AFFORD)
    post_purchase = any(rx.search(norm) for rx in _POST)
    compliment = any(rx.search(norm) for rx in _COMPL)
    hedged = bool(_HEDGE.search(norm))

    signals = sorted(high_hits) + sorted(medium_hits - high_hits)
    if afford:
        signals.append("affordability_barrier")
    if post_purchase:
        signals.append("post_purchase_feedback")
    if compliment:
        signals.append("compliment")
    if negated_any:
        signals.append("negated_purchase")
    sig = tuple(signals)

    if high_hits:
        return IntentResult("high", sig, "explicit purchase request or inquiry", negated_any)
    if post_purchase:
        # Complaint or confirmation about a past order: evidence of customers,
        # not of new purchase intent. Reported separately.
        return IntentResult("no_signal", sig, "post-purchase feedback, not new intent", negated_any)
    if afford:
        return IntentResult("low", sig, "product interest with stated affordability barrier", negated_any)
    if medium_hits:
        if hedged:
            return IntentResult("uncertain", sig, "hedged or hypothetical shopping language", negated_any)
        if medium_hits == {"shopping_term"} and negated_any:
            return IntentResult("no_signal", sig, "shopping word only in a negated phrase", True)
        return IntentResult("medium", sig, "weaker shopping signal without a clear request", negated_any)
    if negated_any:
        return IntentResult("no_signal", sig, "explicitly negated purchase", True)
    if CONTACT.search(norm):
        return IntentResult("uncertain", sig + ("contact_request",), "DM/contact mention without a stated purpose", False)
    if compliment:
        return IntentResult("low", sig, "compliment or product interest, no buying request", False)
    return IntentResult("no_signal", sig, "no purchase-related cue", False)


# ── Seller-side caption signals (NOT purchase intent) ───────────────────────

CAPTION_SIGNALS = {
    "shows_price": [r"₦\s?\d", r"\bprice\s*:", r"\bngn\s?\d", r"\b\d{2,3}(,\d{3})+\s*(naira|ngn)\b"],
    "call_to_action": [r"\bshop\b", r"\bdm (to|for) (order|price|enquir)", r"\blink in (our )?bio\b", r"\border (now|today|yours)\b",
                       r"\bvisit (us|our)\b", r"\bavailable (now|in store|online)\b", r"\bwww\.|\.com\b", r"\bwhatsapp\b"],
    "launch_or_restock": [r"\bnew (collection|drop|arrivals?|in)\b", r"\brestock", r"\bjust dropped\b", r"\bout now\b", r"\bpre-?order\b"],
}
_CAPTION_COMPILED = {k: [re.compile(p) for p in v] for k, v in CAPTION_SIGNALS.items()}


def caption_signals(caption) -> dict[str, bool]:
    """Detect what the *brand* is doing in its caption (pricing, CTA, launch)."""
    t = clean_text(caption).lower()
    return {name: any(rx.search(t) for rx in rxs) for name, rxs in _CAPTION_COMPILED.items()}
