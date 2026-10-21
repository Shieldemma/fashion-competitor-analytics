# Intent Classifier Evaluation (auto-generated)

Classifier: `fashion_intel/intent.py` (rule-based). Definitions: `docs/intent_taxonomy.md`.

**Read this before quoting any number.** The real-comment labels were drafted by the AI assistant *without* seeing classifier output, but they have **not yet been reviewed by a human**. Fill the `human_label` column in `data/evaluation/real_comments_labelled.csv` and re-run `python -m fashion_intel evaluate` to get human-validated scores.

## real_random (n = 150; gold labels: assistant_draft_blind)

Exact-label accuracy: **90.7%** (dominated by the easy no_signal/low majority — see per-class table).

### Purchase signal (high + medium) vs everything else

| positives_true | positives_pred | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|---|
| 4 | 5 | 4 | 1 | 0 | 0.8 | 1 | 0.89 |

### Per class

| label | support | predicted | precision | recall | f1 |
|---|---|---|---|---|---|
| high | 2 | 2 | 1 | 1 | 1 |
| medium | 2 | 3 | 0.67 | 1 | 0.8 |
| low | 50 | 42 | 0.95 | 0.8 | 0.87 |
| no_signal | 91 | 100 | 0.89 | 0.98 | 0.93 |
| uncertain | 5 | 3 | 1 | 0.6 | 0.75 |

### Confusion matrix (rows = gold, columns = predicted)

| true | high | medium | low | no_signal | uncertain |
|---|---|---|---|---|---|
| high | 2 | 0 | 0 | 0 | 0 |
| medium | 0 | 2 | 0 | 0 | 0 |
| low | 0 | 1 | 40 | 9 | 0 |
| no_signal | 0 | 0 | 2 | 89 | 0 |
| uncertain | 0 | 0 | 0 | 2 | 3 |

### Disagreements

| text | gold | predicted | signals |
|---|---|---|---|
| This gal can create, we need this pieces in future. The museum for this dresses pleass we  | low | medium | desire |
| Mama on 🔥🔥🔥😍🥰 | low | no_signal |  |
| @_pd.cakesandchops I'm sat 😍😩👏🔥🔥🔥 like whaaaaatttttt 🫢 | low | no_signal |  |
| This team 🙌❤️ | low | no_signal |  |
| Oh my Goodness! 😍😍😍😍 | low | no_signal |  |
| The voice 😍😍 | low | no_signal |  |
| 😩 if only 😍 | uncertain | no_signal |  |
| I have the top u made with this fabric 😍 | no_signal | low | compliment |
| Shirt ⬆️ | uncertain | no_signal |  |
| Dear Ashluxe My name is Ayoade, and I'm a growing streetwear and fashion content creator w | no_signal | low | compliment |
| The Blueprint !!! | low | no_signal |  |
| 100 over 100 | low | no_signal |  |
| This feels like a proper editorial 🔥 | low | no_signal |  |
| @_laboomz 🔥🔥🔥🔥 edit as usual | low | no_signal |  |

## real_all (n = 170; gold labels: assistant_draft_blind)

Exact-label accuracy: **88.2%** (dominated by the easy no_signal/low majority — see per-class table).

### Purchase signal (high + medium) vs everything else

| positives_true | positives_pred | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 1 | 2 | 0.88 | 0.78 | 0.82 |

### Per class

| label | support | predicted | precision | recall | f1 |
|---|---|---|---|---|---|
| high | 5 | 4 | 1 | 0.8 | 0.89 |
| medium | 4 | 4 | 0.75 | 0.75 | 0.75 |
| low | 56 | 50 | 0.9 | 0.8 | 0.85 |
| no_signal | 99 | 108 | 0.87 | 0.95 | 0.91 |
| uncertain | 6 | 4 | 1 | 0.67 | 0.8 |

### Confusion matrix (rows = gold, columns = predicted)

| true | high | medium | low | no_signal | uncertain |
|---|---|---|---|---|---|
| high | 4 | 0 | 0 | 1 | 0 |
| medium | 0 | 3 | 0 | 1 | 0 |
| low | 0 | 1 | 45 | 10 | 0 |
| no_signal | 0 | 0 | 5 | 94 | 0 |
| uncertain | 0 | 0 | 0 | 2 | 4 |

### Disagreements

| text | gold | predicted | signals |
|---|---|---|---|
| This gal can create, we need this pieces in future. The museum for this dresses pleass we  | low | medium | desire |
| Mama on 🔥🔥🔥😍🥰 | low | no_signal |  |
| @_pd.cakesandchops I'm sat 😍😩👏🔥🔥🔥 like whaaaaatttttt 🫢 | low | no_signal |  |
| This team 🙌❤️ | low | no_signal |  |
| Oh my Goodness! 😍😍😍😍 | low | no_signal |  |
| The voice 😍😍 | low | no_signal |  |
| 😩 if only 😍 | uncertain | no_signal |  |
| I have the top u made with this fabric 😍 | no_signal | low | compliment |
| Shirt ⬆️ | uncertain | no_signal |  |
| Dear Ashluxe My name is Ayoade, and I'm a growing streetwear and fashion content creator w | no_signal | low | compliment |
| The Blueprint !!! | low | no_signal |  |
| 100 over 100 | low | no_signal |  |
| This feels like a proper editorial 🔥 | low | no_signal |  |
| @_laboomz 🔥🔥🔥🔥 edit as usual | low | no_signal |  |
| Will this be restocked | high | no_signal |  |
| Dear Ashluxe My name is Ayoade, and I'm a growing streetwear and fashion content creator w | no_signal | low | compliment |
| Guys this shirt we need | medium | no_signal |  |
| 'You could like something at first sight, but to say you love it, you need to give it some | no_signal | low | compliment |
| Needs to be televised 🔥 | low | no_signal |  |
| I've written my debut YA novel, 'Sometime in May', and if I could shoot it as a movie, I'd | no_signal | low | compliment |

## challenge_synthetic (n = 55; gold labels: synthetic_handwritten)

Exact-label accuracy: **100.0%** (dominated by the easy no_signal/low majority — see per-class table).

### Purchase signal (high + medium) vs everything else

| positives_true | positives_pred | tp | fp | fn | precision | recall | f1 |
|---|---|---|---|---|---|---|---|
| 31 | 31 | 31 | 0 | 0 | 1 | 1 | 1 |

### Per class

| label | support | predicted | precision | recall | f1 |
|---|---|---|---|---|---|
| high | 25 | 25 | 1 | 1 | 1 |
| medium | 6 | 6 | 1 | 1 | 1 |
| low | 8 | 8 | 1 | 1 | 1 |
| no_signal | 13 | 13 | 1 | 1 | 1 |
| uncertain | 3 | 3 | 1 | 1 | 1 |

### Confusion matrix (rows = gold, columns = predicted)

| true | high | medium | low | no_signal | uncertain |
|---|---|---|---|---|---|
| high | 25 | 0 | 0 | 0 | 0 |
| medium | 0 | 6 | 0 | 0 | 0 |
| low | 0 | 0 | 8 | 0 | 0 |
| no_signal | 0 | 0 | 0 | 13 | 0 |
| uncertain | 0 | 0 | 0 | 0 | 3 |

## Limitations

- The real sample has very few high/medium examples (single digits), so their precision/recall have very wide uncertainty: one extra error moves recall by 20+ points.
- The keyword-enriched rows were selected with a keyword list that overlaps the classifier's rules. That inflates recall on `real_all`, so use `real_random` for representative numbers.
- The rules were written by the same author who drafted the labels. Independent human labelling (ideally two annotators, with agreement measured) is needed for a trustworthy estimate.
- The challenge set is synthetic and was written alongside the rules. Its score is a regression check, not an accuracy estimate.
- Comments come from 4 Instagram accounts over a few months. Performance on other brands, platforms, or more Pidgin-heavy audiences is unknown.
