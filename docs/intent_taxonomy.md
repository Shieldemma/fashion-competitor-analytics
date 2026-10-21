# Purchase-Intent Taxonomy

Unit of analysis: **one audience comment**. Brand and collaborator replies are excluded.
The classifier is `fashion_intel/intent.py`. Try it with `python -m fashion_intel classify "your text"`.

Why comments and not captions: a caption that says "DM to order" measures what the **seller** does.
Customer purchase intent shows up in what the **audience** writes. The v1 project classified captions,
which mostly measured copywriting style. Caption behaviour is still reported, as seller-side signals.

## Labels

| Label | Definition | Examples |
|---|---|---|
| **high** | Explicit request or question about **price, ordering/booking, availability/size/restock, delivery/shipping, or payment** | "How much is this dress?" · "Please, do you deliver to Ikot Ekpene?" · "I want to order this outfit." · "Where can I get this?" · "Wetin be the price?" · "Una dey deliver to Abuja?" · "I wan buy am" · "How do I book" |
| **medium** | Weaker shopping signal **without a clear request**: desire for the item, product-attribute questions, intent to wear, asking a designer to make something | "I need this" · "My next birthday outfit" · "What fabric is this?" · "Am wearing this soon" · "You need to do my wedding gown" |
| **low** (product interest) | Compliment, inspiration or general interest with **no buying request**. Includes stated affordability barriers | "This dress is beautiful." · "Stunning 🔥" · "I love it but cannot afford it." · "This is hard o" |
| **uncertain** | A possible shopping cue whose meaning the rules can't settle: bare fragments, hedged or hypothetical talk, DM/contact mentions with no stated purpose | "where?" · "link?" · "Location?" · "Maybe I'll get one later" · "check your DM" · "I need your contact" |
| **no_signal** | No purchase cue; **explicitly negated** purchase; **post-purchase feedback** (a past order, not new intent); empty, emoji-only or @mention-only text | "Amen" · "I don't want to buy this." · "The delivery was terrible." · "I never received my order" · "😍🔥" · "" |

### Deliberate decisions (and why)

- **Compliments are never purchase intent.** "Gorgeous!" is engagement, not demand.
- **Emoji-only comments are `no_signal` for intent**, though they can still carry positive *sentiment*. An emoji gives no evidence about buying.
- **"I love it but cannot afford it" is `low`** and tagged `affordability_barrier`. It shows interest plus an explicit inability to buy now. These are counted separately as a price-sensitivity indicator.
- **"The delivery was terrible" is `no_signal`** and tagged `post_purchase_feedback`. It is evidence that someone bought, which is useful, but it is not new purchase intent.
- **DM mentions are `uncertain`** unless the purpose is explicit ("Sent you a DM about the dress" is high). On Instagram a DM can be an order, a collab pitch, or spam.
- **Negated questions stay inquiries.** "Don't you deliver to Enugu?" is high.

## Rule mechanics

1. **Normalise:** lowercase, strip URLs and @mentions, collapse stretched letters ("pleeease" → "please"), expand common spellings (`pls`, `hw`, `wetin`, `u`, `dm'd` …).
2. **No letters left?** Then `no_signal` (empty / emoji / mention-only).
3. **Bare ambiguous fragment?** Then `uncertain`.
4. **Per sentence,** match high and medium pattern groups with **word boundaries** (`cost` ≠ `costume`, `dm` ≠ `admin`, `price` ≠ `priceless`).
5. **Negation:** a cue preceded within ~3 words by `don't / not / never / no / can't / won't / i no / no wan …` is cancelled, unless the sentence is a question. "can't wait" and "why not" are not negations.
6. **Hedging** ("maybe", "thinking of", "not sure") in a non-question sentence turns a high cue into `uncertain`.
7. **Priority:** high → post-purchase → affordability → medium (or uncertain if hedged) → negated → contact mention → compliment → no_signal.
8. **Repeated signals** count once per type (`intent_signal_count`). "How much? How much?" is one signal, while "How much, and do you deliver?" is two.

## Nigerian English and Pidgin coverage

Covered: `wetin be the price`, `how much be`, `last price`, `price abeg / biko`, `i wan buy`, `i go buy`, `make i order`, `i fit get am`, `una dey deliver / una get`, `e still dey?`, `waybill`, `pay on delivery`, `account number / acct`, and negation `i no wan buy`.

Not covered (known gaps): Yoruba, Igbo and Hausa text; heavy code-switching; sarcasm ("this price na wa 🙄"); voice notes and images. See `reports/classifier_evaluation.md` for measured performance.
