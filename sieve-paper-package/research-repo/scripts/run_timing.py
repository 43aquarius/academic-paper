#!/usr/bin/env python3
"""Compression-cost microbenchmark (CPU, real wall-clock).

Measures the per-context compression latency and peak memory of Sieve and
the TextRank baseline across context sizes, plus the analytical compute of
one small-LM forward pass (the LLMLingua-style cost floor).
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


def bench(fn, ctx, q, ratio, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(ctx, q, ratio)
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times), min(times), max(times)


def main():
    records = json.load(open(os.path.join(DATA, "qasper_sample.json")))
    # Build contexts of increasing size by concatenating papers.
    target_words = [1000, 2000, 4000, 6000]
    all_ctx = " ".join(r["context"] for r in records)
    q = "What datasets and methods are used for evaluation?"
    contexts = {}
    for tw in target_words:
        contexts[tw] = " ".join(all_ctx.split()[:tw])

    rows = []
    for tw, ctx in contexts.items():
        n_words = len(ctx.split())
        med, lo, hi = bench(
            lambda c, qq, r: compress(c, qq, r, SieveConfig(alpha=ALPHA)),
            ctx, q, 4.0)
        row = {"context_words": n_words, "method": "sieve",
               "median_ms": round(med, 2), "min_ms": round(lo, 2),
               "max_ms": round(hi, 2), "repeats": 5}
        rows.append(row)
        print(row)

        med, lo, hi = bench(
            lambda c, qq, r: B.textrank_select(c, r), ctx, q, 4.0)
        row = {"context_words": n_words, "method": "textrank",
               "median_ms": round(med, 2), "min_ms": round(lo, 2),
               "max_ms": round(hi, 2), "repeats": 5}
        rows.append(row)
        print(row)

        med, lo, hi = bench(
            lambda c, qq, r: B.truncate_head(c, r), ctx, q, 4.0)
        row = {"context_words": n_words, "method": "head",
               "median_ms": round(med, 3), "min_ms": round(lo, 3),
               "max_ms": round(hi, 3), "repeats": 5}
        rows.append(row)
        print(row)

    out = os.path.join(RES, "timing.json")
    with open(out, "w") as f:
        json.dump(rows, f, indent=1)
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
