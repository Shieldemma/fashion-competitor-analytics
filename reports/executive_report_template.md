# [Client] Social Media Competitor Audit: Executive Report

**Prepared for:** [Client] · **Prepared by:** [Analyst] · **Date:** [YYYY-MM-DD]
**Data:** [platforms] collected via [tool] on [collection date] · **Audit window:** [start] → [end]
**Pipeline run:** `[run_id from data/processed/run_manifest.json]`

> Rule for this template: every number must be copied from `reports/findings_generated.md` for the named run.
> Delete any section the data cannot support, and say why. Do not fill it with assumptions.

## 1. Question and answer
- **Question:** [the client's decision, e.g. "Which platform should get more budget?"]
- **Answer in one sentence:** [what the evidence supports, including "cannot be determined from this data" if true]

## 2. Coverage
| Competitor | Platforms collected | Posts in window | Sampled comments | Gaps |
|---|---|---|---|---|
| [ ] | [ ] | [ ] | [ ] | [ ] |

## 3. Findings (each with its denominator and uncertainty)
1. **[Finding]:** [number] ([numerator]/[denominator], 95% CI [x–y]%). *So what:* [business meaning].
2. …

## 4. Robustness
[Does the conclusion survive excluding collab posts, pinned posts and emoji-only comments, and using all posts instead of the window? Copy the sensitivity table.]

## 5. What this cannot tell you
- Signals ≠ purchases: [state whether any sales, conversion or spend data was available]
- Observational, not causal: [main confounders]
- [Other gaps]

## 6. Recommendation
[Only what the evidence supports. If a budget split is not supported, recommend the experiment or data collection that would support one: platforms, duration, metric (cost per conversation/order), tracking method.]

## 7. Method
Collection → validation → classification (`docs/intent_taxonomy.md`) → metrics (`docs/data_dictionary.md`). Classifier performance: [copy from `reports/classifier_evaluation.md`, with its caveats].
