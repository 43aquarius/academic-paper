#!/usr/bin/env python3
"""Sample-level correlation between evidence recall and end-task QA F1.

Protocol selection (automatic):
  - expanded   : results/checkpoints/qa_expanded.jsonl, the first 100
                QASPER records of the rebuilt pool (the same records the
                GPT-2 gate ran on), methods incl. BM25. Used when every
                selector method has >= 80 successful records.
  - conference : results/checkpoints/main.jsonl (n=25 protocol) on
                data/qasper_sample.json records 10:35.

For each (record, selector-method) pair with locatable gold evidence we
compute per-record evidence recall (index-level, same as the selector
protocol) and the QA F1 of that method on that record, then report
Pearson and Spearman correlations pooled and per method.
Output: results/correlation.json
"""
import json
import math
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))

from sieve.sentence_split import split_sentences   # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from run_journal_analysis import record_recall     # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")

SELECTORS = ["head", "random", "stride", "textrank", "sieve", "bm25"]


def pearson(x, y):
    n = len(x)
    mx, my = statistics.mean(x), statistics.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sum((a - mx) ** 2 for a in x) *
                    sum((b - my) ** 2 for b in y))
    return num / den if den else float("nan")


def spearman(x, y):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(x), ranks(y))


def load_expanded():
    """Return (qa, test_records) for the expanded protocol or None."""
    path = os.path.join(RES, "checkpoints", "qa_expanded.jsonl")
    if not os.path.exists(path):
        return None
    qa = {}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ok") and r.get("exp") == "main":
            qa[(r["method"], r["id"])] = r
    cnt = {m: sum(1 for (mm, _), v in qa.items() if mm == m)
           for m in SELECTORS}
    if any(cnt[m] < 80 for m in SELECTORS):
        return None
    pool = json.load(open(os.path.join(DATA, "pool_qasper.json")))
    return qa, pool[:100]


def load_conference():
    path = os.path.join(RES, "checkpoints", "main.jsonl")
    qa = {}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ok") and r.get("exp") == "main":
            qa[(r["method"], r["example"])] = r
    qs = json.load(open(os.path.join(DATA, "qasper_sample.json")))
    return qa, qs[10:35]


def main():
    exp = load_expanded()
    if exp is not None:
        qa, test, protocol = exp[0], exp[1], "expanded"
    else:
        qa, test = load_conference()
        protocol = "conference"

    pairs = []       # (recall, f1, method)
    per_method = {}
    n_used = 0
    for rec in test:
        if not rec.get("evidence"):
            continue
        rid = rec["id"]
        has_any = False
        for m in SELECTORS:
            key = (m, rid)
            if key not in qa:
                continue
            rc = record_recall(rec, m, 4.0)
            if rc is None:
                continue
            pairs.append((rc * 100.0, qa[key]["f1"] * 100.0, m))
            per_method.setdefault(m, []).append(
                (rc * 100.0, qa[key]["f1"] * 100.0))
            has_any = True
        if has_any:
            n_used += 1

    out = {"protocol": protocol, "n_records": n_used,
           "n_test_split": len(test), "n_pairs": len(pairs)}
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    out["pooled"] = {
        "pearson": pearson(xs, ys),
        "spearman": spearman(xs, ys),
        "n": len(pairs),
    }
    out["per_method"] = {}
    for m, vals in per_method.items():
        out["per_method"][m] = {
            "pearson": pearson([v[0] for v in vals], [v[1] for v in vals]),
            "spearman": spearman([v[0] for v in vals], [v[1] for v in vals]),
            "n": len(vals),
            "mean_recall": statistics.mean(v[0] for v in vals),
            "mean_f1": statistics.mean(v[1] for v in vals),
        }
    out["pairs"] = pairs

    dst = os.path.join(RES, "correlation.json")
    json.dump(out, open(dst, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "pairs"},
                     indent=1))
    print("saved", dst)


if __name__ == "__main__":
    main()
