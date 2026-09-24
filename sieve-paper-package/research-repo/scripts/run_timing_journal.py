#!/usr/bin/env python3
"""Journal-version compression-cost microbenchmark (CPU, same container).

All methods, same synthetic contexts (1k/2k/4k/6k words built by
concatenating QASPER records), median of 5 runs after one warm-up:

  sieve, textrank, head, random, stride, bm25, gpt2-gate

The GPT-2 gate timing is reported separately because each run costs
seconds; the gate is benchmarked with 3 repeats on the same contexts.
Output: results/timing_journal.json
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
import baselines as B                         # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
ALPHA = 0.3
DST = os.path.join(RES, "timing_journal.json")


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
        cheap = {
            "sieve": lambda: compress(ctx, q, 4.0, SieveConfig(alpha=ALPHA)),
            "textrank": lambda: B.textrank_select(ctx, 4.0),
            "head": lambda: B.truncate_head(ctx, 4.0),
            "random": lambda: B.random_select(ctx, 4.0, seed=0),
            "stride": lambda: B.stride_select(ctx, 4.0),
            "bm25": lambda: B.bm25_select(ctx, q, 4.0),
        }
        for name, fn in cheap.items():
            med, lo, hi = bench(fn, repeats=5)
            row = {"context_words": n_words, "method": name,
                   "median_ms": round(med, 2), "min_ms": round(lo, 2),
                   "max_ms": round(hi, 2), "repeats": 5}
            rows.append(row)
            print(row)

    # GPT-2 gate on the same contexts (3 repeats)
    if "--gate" in sys.argv:
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import run_gpt2_gate as G
        G.load_model()
        from sieve.sentence_split import split_sentences
        for tw, ctx in contexts.items():
            sents = split_sentences(ctx)

            def gate_run():
                G.score_sentences(sents, q)
            med, lo, hi = bench(gate_run, repeats=3)
            row = {"context_words": len(ctx.split()), "method": "gpt2-gate",
                   "median_ms": round(med, 1), "min_ms": round(lo, 1),
                   "max_ms": round(hi, 1), "repeats": 3}
            rows.append(row)
            print(row)

    json.dump(rows, open(DST, "w"), indent=1)
    print("saved ->", DST)


if __name__ == "__main__":
    main()
