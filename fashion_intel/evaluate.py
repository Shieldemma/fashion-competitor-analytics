"""Evaluate the intent classifier against labelled examples.

Two labelled sets live in data/evaluation/:
- real_comments_labelled.csv: real audience comments. 150 random + 20
  keyword-enriched (to give the rare high/medium classes some support).
  Labels were drafted blind (without seeing classifier output) by the AI
  assistant against docs/intent_taxonomy.md. Fill `human_label` to override;
  this script uses human_label wherever it is present.
- challenge_set.csv: hand-written synthetic edge cases (required examples,
  Pidgin, negation, word-boundary traps). Useful as a regression test, NOT as
  an estimate of real-world accuracy.

Writes reports/classifier_evaluation.md and data/evaluation/predictions.csv.
"""

from __future__ import annotations

import pandas as pd

from .config import EVAL_DIR, REPORTS_DIR
from .intent import LABELS, classify
from .report import md_table

POSITIVE = {"high", "medium"}


def per_class(y_true: pd.Series, y_pred: pd.Series) -> pd.DataFrame:
    rows = []
    for lab in LABELS:
        tp = int(((y_pred == lab) & (y_true == lab)).sum())
        fp = int(((y_pred == lab) & (y_true != lab)).sum())
        fn = int(((y_pred != lab) & (y_true == lab)).sum())
        p = tp / (tp + fp) if tp + fp else float("nan")
        r = tp / (tp + fn) if tp + fn else float("nan")
        f1 = 2 * p * r / (p + r) if (p == p and r == r and p + r) else float("nan")
        rows.append({"label": lab, "support": int((y_true == lab).sum()), "predicted": int((y_pred == lab).sum()),
                     "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)})
    return pd.DataFrame(rows)


def binary(y_true: pd.Series, y_pred: pd.Series) -> dict:
    t, p = y_true.isin(POSITIVE), y_pred.isin(POSITIVE)
    tp, fp, fn = int((t & p).sum()), int((~t & p).sum()), int((t & ~p).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (prec == prec and rec == rec and prec + rec) else float("nan")
    return {"positives_true": int(t.sum()), "positives_pred": int(p.sum()), "tp": tp, "fp": fp, "fn": fn,
            "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)}


def confusion(y_true: pd.Series, y_pred: pd.Series) -> pd.DataFrame:
    m = pd.crosstab(y_true.rename("true"), y_pred.rename("predicted")).reindex(index=LABELS, columns=LABELS, fill_value=0)
    return m.reset_index()


def load_sets() -> dict[str, pd.DataFrame]:
    real = pd.read_csv(EVAL_DIR / "real_comments_labelled.csv", keep_default_na=False)
    real["gold"] = real["human_label"].where(real["human_label"].str.strip() != "", real["label"])
    real["gold_source"] = real["human_label"].map(lambda v: "human" if str(v).strip() else "assistant_draft_blind")
    challenge = pd.read_csv(EVAL_DIR / "challenge_set.csv", keep_default_na=False)
    challenge["gold"] = challenge["label"]
    challenge["gold_source"] = "synthetic_handwritten"
    return {
        "real_random": real[real["sample"] == "random"].copy(),
        "real_all": real.copy(),
        "challenge_synthetic": challenge,
    }


def evaluate() -> tuple[str, pd.DataFrame]:
    sets = load_sets()
    parts = ["# Intent Classifier Evaluation (auto-generated)\n",
             "Classifier: `fashion_intel/intent.py` (rule-based). Definitions: `docs/intent_taxonomy.md`.\n",
             "**Read this before quoting any number.** The real-comment labels were drafted by the AI assistant "
             "*without* seeing classifier output, but they have **not yet been reviewed by a human**. "
             "Fill the `human_label` column in `data/evaluation/real_comments_labelled.csv` and re-run "
             "`python -m fashion_intel evaluate` to get human-validated scores.\n"]
    all_preds = []
    for name, df in sets.items():
        results = df["text"].map(classify)
        df["predicted"] = results.map(lambda r: r.label)
        df["signals"] = results.map(lambda r: "|".join(r.signals))
        df["set"] = name
        all_preds.append(df)
        sources = ", ".join(sorted(df["gold_source"].unique()))
        acc = (df["gold"] == df["predicted"]).mean()
        parts += [f"## {name} (n = {len(df)}; gold labels: {sources})\n",
                  f"Exact-label accuracy: **{acc:.1%}** (dominated by the easy no_signal/low majority — see per-class table).\n",
                  "### Purchase signal (high + medium) vs everything else\n", md_table(pd.DataFrame([binary(df['gold'], df['predicted'])])),
                  "### Per class\n", md_table(per_class(df["gold"], df["predicted"])),
                  "### Confusion matrix (rows = gold, columns = predicted)\n", md_table(confusion(df["gold"], df["predicted"]))]
        wrong = df[df["gold"] != df["predicted"]]
        if len(wrong):
            parts += ["### Disagreements\n", md_table(wrong[["text", "gold", "predicted", "signals"]].assign(
                text=wrong["text"].str.slice(0, 90)), max_rows=40)]
    parts += ["## Limitations\n",
              "- The real sample has very few high/medium examples (single digits), so their precision/recall have "
              "very wide uncertainty: one extra error moves recall by 20+ points.",
              "- The keyword-enriched rows were selected with a keyword list that overlaps the classifier's rules. "
              "That inflates recall on `real_all`, so use `real_random` for representative numbers.",
              "- The rules were written by the same author who drafted the labels. Independent human labelling "
              "(ideally two annotators, with agreement measured) is needed for a trustworthy estimate.",
              "- The challenge set is synthetic and was written alongside the rules. Its score is a regression check, "
              "not an accuracy estimate.",
              "- Comments come from 4 Instagram accounts over a few months. Performance on other brands, platforms, "
              "or more Pidgin-heavy audiences is unknown.\n"]
    text = "\n".join(parts)
    (REPORTS_DIR / "classifier_evaluation.md").write_text(text, encoding="utf-8")
    preds = pd.concat(all_preds, ignore_index=True)
    preds[["set", "text", "gold", "gold_source", "predicted", "signals"]].to_csv(EVAL_DIR / "predictions.csv", index=False)
    return text, preds


def main() -> None:
    text, preds = evaluate()
    for name, df in preds.groupby("set", sort=False):
        b = binary(df["gold"], df["predicted"])
        print(f"{name:22} n={len(df):4}  purchase-signal P={b['precision']} R={b['recall']} F1={b['f1']}  "
              f"exact-acc={(df['gold'] == df['predicted']).mean():.1%}")
    print(f"\nFull report: {REPORTS_DIR / 'classifier_evaluation.md'}")
