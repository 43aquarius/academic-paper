#!/usr/bin/env python3
"""E5: selector-level redundancy metrics (pre-registered in E5_PREREG.md).

Measures, per pool record / method / ratio, on the selected sentence set:
  M-A  selected-set self-similarity (mean pairwise IDF-cosine; the
       quantity beta penalizes) -- objective-space metric
  M-B  duplicate content-token rate DR of the emitted text
       (1 - distinct/total content tokens) -- token-level metric
  M-C  emitted word count (budget-matching sanity gate)

Methods (configs identical to run_journal_analysis.py):
  sieve          alpha=0.3, beta=0.3, floor=0.35, power=1.5
  sieve-nored    alpha=0.3, beta=0.0, floor=0.35, power=1.5
  sieve-relonly  alpha=1.0, beta=0.0, floor=1.0, power=1.5
  bm25           baselines.bm25_idx(context, question, ratio)

No LLM calls; pure local compute. Resumable: cells (dataset x method x
ratio) are checkpointed to results/redundancy_metric.json after each
cell; a time guard (~230s) exits cleanly so the driver can re-invoke.
Aggregates + paired bootstrap intervals are computed in a final stage
only when every cell is complete.
"""
import json
import os
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))

from sieve.scoring import base_scores          # noqa: E402
from sieve.selector import select              # noqa: E402
from sieve.sentence_split import split_sentences  # noqa: E402
from sieve.tokens import content_tokens, tokenize, cosine_sparse  # noqa: E402
import baselines as B                          # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
CKPT = os.path.join(RES, "redundancy_metric.json")

POOLS = [("qasper", "pool_qasper.json"),
         ("hotpot", "pool_hotpot.json"),
         ("2wiki", "pool_2wiki.json")]
RATIOS = [2.0, 4.0, 8.0, 16.0]
METHODS = ["sieve", "sieve-nored", "sieve-relonly", "bm25"]
METHOD_CFG = {
    "sieve": {"alpha": 0.3, "beta": 0.3, "floor": 0.35, "power": 1.5},
    "sieve-nored": {"alpha": 0.3, "beta": 0.0, "floor": 0.35, "power": 1.5},
    "sieve-relonly": {"alpha": 1.0, "beta": 0.0, "floor": 1.0, "power": 1.5},
}
N_BOOT = 1000
SEED = 20260923  # same as make_numbers_journal.py: bit-stable
TIME_GUARD_S = 230.0


def load_ckpt():
    if os.path.exists(CKPT):
        try:
            return json.load(open(CKPT))
        except Exception:
            pass
    return {}


def save_ckpt(out):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f)
    os.replace(tmp, CKPT)


def record_metrics(sents, counters, idf, kept):
    """M-A / M-B / M-C for one selected set. Definitions frozen in
    E5_PREREG.md: selfsim := 0 when fewer than two sentences are
    selected; DR := 0 when the emitted text has no content tokens."""
    kept = sorted(set(kept))
    if len(kept) >= 2:
        sims = []
        for a in range(len(kept)):
            for b in range(a + 1, len(kept)):
                sims.append(cosine_sparse(counters[kept[a]],
                                           counters[kept[b]], idf))
        sim = statistics.mean(sims)
    else:
        sim = 0.0
    text = " ".join(sents[i] for i in kept)
    toks = content_tokens(tokenize(text))
    dr = 1.0 - len(set(toks)) / len(toks) if toks else 0.0
    return {"sim": sim, "dr": dr, "words": len(text.split())}


def cell(records, method, ratio):
    vals = {}
    for rec in records:
        ctx, q = rec["context"], rec["question"]
        sents = split_sentences(ctx)
        if not sents:
            continue
        if method == "bm25":
            _, counters, _, idf = base_scores(sents, q, 0.3, 0.35, 1.5)
            kept = B.bm25_idx(ctx, q, ratio)
        else:
            cfg = METHOD_CFG[method]
            scores, counters, _, idf = base_scores(
                sents, q, cfg["alpha"], cfg["floor"], cfg["power"])
            budget = max(1, int(sum(len(s.split()) for s in sents) / ratio))
            kept = select(sents, scores, counters, idf, budget, cfg["beta"])
        vals[rec["id"]] = record_metrics(sents, counters, idf, kept)
    return vals


def boot(vals, seed=SEED):
    rng = random.Random(seed)
    n = len(vals)
    means = []
    for _ in range(N_BOOT):
        s = [vals[rng.randrange(n)] for _ in vals]
        means.append(statistics.mean(s))
    means.sort()
    return means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT)]


def paired_ci(pairs, seed=SEED):
    rng = random.Random(seed)
    diffs = [a - b for a, b in pairs]
    n = len(diffs)
    means = []
    for _ in range(N_BOOT):
        s = [diffs[rng.randrange(n)] for _ in diffs]
        means.append(statistics.mean(s))
    means.sort()
    return means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT)]


def main():
    t0 = time.time()
    out = load_ckpt()
    out.setdefault("per_record", {})
    out["protocol"] = {
        "n_boot": N_BOOT, "seed": SEED, "ratios": RATIOS,
        "methods": METHODS, "prereg": "E5_PREREG.md"}

    pool_cache = {}
    complete = True
    for ds, path in POOLS:
        cells_needed = []
        out["per_record"].setdefault(ds, {})
        for m in METHODS:
            out["per_record"][ds].setdefault(m, {})
            for r in RATIOS:
                if str(r) not in out["per_record"][ds][m]:
                    cells_needed.append((m, r))
        if not cells_needed:
            continue
        if ds not in pool_cache:
            pool_cache[ds] = json.load(open(os.path.join(DATA, path)))
            print(f"pool {ds}: {len(pool_cache[ds])} records")
        records = pool_cache[ds]
        for m, r in cells_needed:
            if time.time() - t0 > TIME_GUARD_S:
                complete = False
                break
            tc = time.time()
            vals = cell(records, m, r)
            out["per_record"][ds][m][str(r)] = vals
            save_ckpt(out)
            print(f"cell {ds:7s} {m:14s} r={r:4.1f} n={len(vals)} "
                  f"({time.time() - tc:.0f}s, total {time.time() - t0:.0f}s)")
        if time.time() - t0 > TIME_GUARD_S:
            complete = False
            break

    # ---- final stage: aggregates + paired intervals ----
    all_done = all(
        str(r) in out["per_record"].get(ds, {}).get(m, {})
        for ds, _ in POOLS for m in METHODS for r in RATIOS)
    if all_done:
        out["summary"] = {}
        for ds, _ in POOLS:
            out["summary"][ds] = {}
            for r in RATIOS:
                rs = str(r)
                agg = {"methods": {}, "paired": {}}
                for m in METHODS:
                    per = out["per_record"][ds][m][rs]
                    entry = {}
                    for met in ("sim", "dr"):
                        vals = [v[met] for v in per.values()]
                        lo, hi = boot(vals)
                        entry[met] = {"mean": statistics.mean(vals),
                                      "ci": [lo, hi], "n": len(vals)}
                    entry["words"] = {
                        "mean": statistics.mean(
                            v["words"] for v in per.values())}
                    agg["methods"][m] = entry
                per_s = out["per_record"][ds]["sieve"][rs]
                per_n = out["per_record"][ds]["sieve-nored"][rs]
                common = sorted(set(per_s) & set(per_n))
                for met in ("sim", "dr", "words"):
                    pairs = [(per_s[i][met], per_n[i][met]) for i in common]
                    d = statistics.mean(a - b for a, b in pairs)
                    lo, hi = paired_ci(pairs)
                    agg["paired"][met] = {"mean": d, "ci": [lo, hi],
                                          "n": len(pairs)}
                out["summary"][ds][rs] = agg
                p = agg["paired"]
                print(f"summary {ds:7s} r={r:4.1f} "
                      f"sim d={p['sim']['mean']:+.4f} "
                      f"CI=[{p['sim']['ci'][0]:+.4f},{p['sim']['ci'][1]:+.4f}] "
                      f"dr d={p['dr']['mean']:+.4f} "
                      f"CI=[{p['dr']['ci'][0]:+.4f},{p['dr']['ci'][1]:+.4f}] "
                      f"words d={p['words']['mean']:+.1f}")
        save_ckpt(out)
        print("ALL DONE (cells + summary)")
        return
    if complete:
        # cells finished within this invocation but guard tripped between
        # pools; summary not yet computed -- re-invoke to finish
        save_ckpt(out)
        print("CELLS DONE, summary pending: re-invoke this script")
    else:
        print("TIME GUARD: re-invoke this script to resume")


if __name__ == "__main__":
    main()
