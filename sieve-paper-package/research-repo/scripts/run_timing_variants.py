#!/usr/bin/env python3
"""CPU microbenchmark for the five Sieve ablation variants (Path C).

Same protocol as run_timing_journal.py (same synthetic contexts built by
concatenating the first 30 QASPER pool records, same question, median of
5 runs after one warm-up), so the numbers are directly comparable with
results/timing_journal.json. The five configurations match exactly the
variant semantics of run_journal_analysis.kept_indices:

  sieve          alpha=0.3                 (full configuration)
  sieve-noq      alpha=0.0                 (no question conditioning)
  sieve-nopos    alpha=0.3, floor=1.0      (flat positional prior)
  sieve-nored    alpha=0.3, beta=0.0       (no redundancy penalty)
  sieve-relonly  alpha=1.0, floor=1.0, beta=0.0  (relevance only)

Output: results/timing_variants.json (same row format as
timing_journal.json). Pure local compute, no LLM calls.
"""
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))

from sieve import compress, SieveConfig       # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
DST = os.path.join(RES, "timing_variants.json")

VARIANTS = {
    "sieve": dict(alpha=0.3),
    "sieve-noq": dict(alpha=0.0),
    "sieve-nopos": dict(alpha=0.3, floor=1.0),
    "sieve-nored": dict(alpha=0.3, beta=0.0),
    "sieve-relonly": dict(alpha=1.0, floor=1.0, beta=0.0),
}


def bench(fn, repeats=5, warmup=1):
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times), min(times), max(times)


def main():
    records = json.load(open(os.path.join(DATA, "pool_qasper.json")))
    all_ctx = " ".join(r["context"] for r in records[:30])
    q = "What datasets and methods are used for evaluation?"
    target_words = [1000, 2000, 4000, 6000]
    contexts = {tw: " ".join(all_ctx.split()[:tw]) for tw in target_words}

    rows = []
    for tw, ctx in contexts.items():
        n_words = len(ctx.split())
        for name, kw in VARIANTS.items():
            cfg = SieveConfig(**kw)
            fn = lambda: compress(ctx, q, 4.0, cfg)  # noqa: E731
            med, lo, hi = bench(fn, repeats=5)
            row = {"context_words": n_words, "method": name,
                   "median_ms": round(med, 2), "min_ms": round(lo, 2),
                   "max_ms": round(hi, 2), "repeats": 5}
            rows.append(row)
            print(row)

    json.dump(rows, open(DST, "w"), indent=1)
    print("saved ->", DST)


if __name__ == "__main__":
    main()
