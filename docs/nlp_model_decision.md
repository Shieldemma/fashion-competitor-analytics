# NLP Approach: Rules Now, a Model Only When Labels Exist

## The question

Would a pretrained Hugging Face model classify purchase intent in these comments better than the transparent rule set?

## What the v1 classifier did (verified in code)

- Two **different** copies of the keyword lists (`analytics/clean_data.py` and `analytics/intent_classifier.py`).
- **Substring** matching: "Nice costume" was labelled High (`cost`), and "admin" matched `dm`.
- No negation: "I don't want to buy this" was labelled Medium.
- Compliment words ("love", "fire", "wow") were counted as intent.
- It was applied to **brand captions**, not audience comments.
- It was never evaluated.

## Options compared

| Option | Fit for this data | Cost / hardware | Reproducibility | Main risk |
|---|---|---|---|---|
| **Rule-based (chosen)** | Explicit patterns for price, order, delivery and Pidgin. Every decision is explainable | Free, CPU, <1 s for 566 comments | Deterministic, no downloads | Misses phrasings nobody wrote a rule for |
| Generic sentiment model (e.g. `cardiffnlp/twitter-roberta-base-sentiment`) | **Wrong task.** Sentiment ≠ purchase intent ("How much?" is neutral, "Gorgeous" is positive) | ~500 MB download, CPU OK | Pinned weights reproducible | Would relabel compliments as intent |
| Zero-shot NLI (e.g. `facebook/bart-large-mnli`) | Can take our label names as prompts, so no training is needed | ~1.6 GB, slow on CPU (rough order: under a second per comment per label set) | Reproducible with pinned revision | Weak on Pidgin and emoji. Unvalidated on Nigerian social text. Hard to explain |
| Fine-tuned multilingual / African model (e.g. `Davlan/afro-xlmr-base`, `castorini/afriberta`) | Best long-term fit for Nigerian English, Pidgin and code-switching | Needs a GPU or patience to train. ~1 GB | Reproducible with a saved checkpoint | **Needs labelled data we don't have** |
| TF-IDF + logistic regression | Cheap and fast | Free | Reproducible | Also needs labels. With 4 positives it would just memorise them |
| Hosted LLM classification | Strong zero-shot | Paid API, per-call cost | Non-deterministic unless pinned | Cost, data-sharing of user comments, drift |

## Evidence

On 150 randomly sampled real audience comments, with labels drafted blind (see caveats):

| Version | Purchase-signal precision | Recall | F1 |
|---|---|---|---|
| Rules, first version (before any tuning) | 0.60 (3/5) | 0.75 (3/4) | 0.67 |
| Rules, after tuning on the error list | 0.80 (4/5) | 1.00 (4/4) | 0.89 |

- The **pre-tuning row is the honest estimate**. The post-tuning row is optimistic, because the fixes were made after seeing these errors (generic fixes only, but still the same sample).
- With **4 true positives**, the 95% interval on recall is roughly **30–95%** before tuning and **51–100%** after. The sample cannot tell a 0.6 classifier from a 0.9 one.
- In the 60-day audit window the classifier finds **0 high/medium** comments in 280. Most comments are emoji or compliments. A model cannot find intent that isn't in the text.

## Decision

**Keep the rule-based classifier as the production component, and do not add a model yet.**

1. The current bottleneck is **data**: one platform, tiny comment samples, and 4 positives. It is not classifier sophistication.
2. A generic sentiment model would be measurably worse for this task, because it conflates praise with intent.
3. Zero-shot and fine-tuned models cannot be **validated** without a larger labelled set, so their output could not be defended to a client.
4. Rules are free, offline, deterministic and explainable. The project stays runnable for any reviewer without multi-GB downloads.

## When to add a model (the upgrade path)

1. **Label ≥ 1,000 comments** with this taxonomy, sampled from more brands and platforms. Use two annotators on a 200-comment overlap and report Cohen's κ.
2. Use the rules as a **pre-filter** to over-sample likely positives for labelling. Keep a random slice for unbiased evaluation.
3. Fine-tune a small African-language-aware encoder (e.g. AfroXLM-R base) on the labelled set. Hold out a test set stratified by brand and platform.
4. **Adopt it only if** it beats the rules on held-out *recall at equal precision* for high + medium. Keep it as an optional component (`intent_model.py`) with the rules as fallback, pinned model revision, and a licence verified on the model card before use.
