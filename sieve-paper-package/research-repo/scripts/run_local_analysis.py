#!/usr/bin/env python3
"""Local (no-API) selector-quality experiments.

E2  evidence recall: fraction of gold evidence sentences retained by each
    compressor at matched budgets, with bootstrap CIs.
E3  selector ablations: evidence recall of Sieve variants (no question,
    no position prior, no redundancy) to attribute the recall.
E4  position robustness: evidence recall as a function of where the
    evidence sits in the context (selector-level analogue of the
    lost-in-the-middle study).

All measurements are computed locally from data/qasper_sample.json records
that carry an evidence field; no LLM calls are involved.
"""
import json
import os
import random
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))

from sieve import compress, SieveConfig          # noqa: E402
from sieve.sentence_split import split_sentences  # noqa: E402
import baselines as B                             # noqa: E402

random.seed(7)
N_BOOT = 1000


def gold_indices(sents, evidence):
    ev_sents = [s.strip() for s in split_sentences(evidence)
                if len(s.split()) > 4]
    if not ev_sents:
        return set()
    idx = set()
    for es in ev_sents:
        for i, s in enumerate(sents):
            if es[:60] == s[:60]:
                idx.add(i)
    return idx


def kept_indices(record, method, ratio=4.0, alpha=0.3):
    ctx, q = record["context"], record["question"]
    sents = split_sentences(ctx)
    if method.startswith("sieve"):
        cfg = SieveConfig(alpha=alpha)
        if method == "sieve-noq":
            cfg.alpha = 0.0
        elif method == "sieve-nopos":
            cfg.floor = 1.0
        elif method == "sieve-nored":
            cfg.beta = 0.0
        elif method == "sieve-relonly":
            cfg.alpha = 1.0
            cfg.floor = 1.0
            cfg.beta = 0.0
        out = compress(ctx, q, ratio, cfg)
        return set(out["kept"])
    # Baselines: recover kept sentence indices by matching text.
    fn = {"head": B.truncate_head, "random": B.random_select,
          "stride": B.stride_select, "textrank": B.textrank_select}[method]
    text = fn(ctx, ratio) if method != "random" \
        else B.random_select(ctx, ratio, seed=0)
    kept = set()
    for i, s in enumerate(sents):
        if s in text:
            kept.add(i)
    return kept


def main():
    pool_path = os.path.join(ROOT, "data", "qasper_recall_pool.json")
    if os.path.exists(pool_path):
        records = json.load(open(pool_path))
        print(f"recall pool: {len(records)} records")
    else:
        records = [r for r in json.load(open(os.path.join(
            ROOT, "data", "qasper_sample.json"))) if r.get("evidence")]
        print(f"records with evidence: {len(records)}")

    def recall(record, method, ratio=4.0, alpha=0.3):
        sents = split_sentences(record["context"])
        gold = gold_indices(sents, record["evidence"])
        if not gold or not sents:
            return None
        kept = kept_indices(record, method, ratio, alpha)
        return len(gold & kept) / len(gold)

    # E2: evidence recall per method
    out = {"methods": {}, "ablations": {}, "position": {}}
    for m in ("sieve", "head", "random", "stride", "textrank"):
        vals = [v for v in (recall(r, m) for r in records) if v is not None]
        means = []
        for _ in range(N_BOOT):
            s = [vals[random.randrange(len(vals))] for _ in vals]
            means.append(statistics.mean(s))
        means.sort()
        out["methods"][m] = {
            "n": len(vals), "recall": statistics.mean(vals),
            "ci": [means[int(0.025 * N_BOOT)],
                   means[int(0.975 * N_BOOT)]],
        }
        print(f"E2 {m:10s} recall={statistics.mean(vals):.3f} "
              f"CI=[{means[int(0.025*N_BOOT)]:.3f},"
              f"{means[int(0.975*N_BOOT)]:.3f}] n={len(vals)}")

    # E3: ablations on recall
    for m in ("sieve", "sieve-noq", "sieve-nopos", "sieve-nored",
              "sieve-relonly"):
        vals = [v for v in (recall(r, m) for r in records) if v is not None]
        out["ablations"][m] = {"n": len(vals),
                               "recall": statistics.mean(vals)}
        print(f"E3 {m:12s} recall={statistics.mean(vals):.3f} "
              f"n={len(vals)}")

    # E4: recall vs evidence position (rebuild context with evidence at
    # controlled relative positions among same-paper filler sentences)
    positions = [0.0, 0.25, 0.5, 0.75, 1.0]
    for pos in positions:
        vals = []
        for rec in records:
            sents = split_sentences(rec["context"])
            ev_sents = [s for s in split_sentences(rec["evidence"])
                        if len(s.split()) > 4]
            if not sents or not ev_sents:
                continue
            anchor = ev_sents[0]
            fillers = [s for s in sents if s != anchor][:40]
            if not fillers:
                continue
            n = len(fillers)
            slot = min(int(round(pos * n)), n)
            ctx = fillers[:slot] + [anchor] + fillers[slot:]
            r2 = {"context": " ".join(ctx), "question": rec["question"],
                  "evidence": anchor}
            v = recall(r2, "sieve")
            if v is not None:
                vals.append(v)
        if vals:
            out["position"][str(pos)] = {
                "n": len(vals), "recall": statistics.mean(vals)}
            print(f"E4 pos={pos:4.2f} sieve recall="
                  f"{statistics.mean(vals):.3f} n={len(vals)}")

    # E6: sensitivity of recall to beta/floor/gamma at r=4
    out["sensitivity"] = {}
    base_cfg = {"beta": 0.3, "floor": 0.35, "gamma": 1.5}  # gamma = code's power

    def recall_cfg(record, beta, floor, gamma):
        sents = split_sentences(record["context"])
        gold = gold_indices(sents, record["evidence"])
        if not gold or not sents:
            return None
        cfg = SieveConfig(alpha=0.3, beta=beta, floor=floor, power=gamma)
        o = compress(record["context"], record["question"], 4.0, cfg)
        kept = set(o["kept"])
        return len(gold & kept) / len(gold)

    for knob, values in (("beta", (0.0, 0.3, 0.6)),
                         ("floor", (0.0, 0.35, 0.7, 1.0)),
                         ("gamma", (0.5, 1.5, 3.0))):
        out["sensitivity"][knob] = {}
        for v in values:
            kw = dict(base_cfg)
            kw[knob] = v
            vals = [x for x in (
                recall_cfg(r, kw["beta"], kw["floor"], kw["gamma"])
                for r in records) if x is not None]
            if vals:
                out["sensitivity"][knob][str(v)] = {
                    "n": len(vals), "recall": statistics.mean(vals)}
                print(f"E6 {knob}={v:4.2f} recall="
                      f"{statistics.mean(vals):.3f} n={len(vals)}")

    # E5: evidence recall vs compression ratio (selector-level sweep)
    ratios = [2.0, 4.0, 8.0, 16.0]
    out["ratio_sweep"] = {}
    for ratio in ratios:
        out["ratio_sweep"][str(ratio)] = {}
        for m in ("sieve", "head", "textrank", "random"):
            vals = [v for v in (recall(r, m, ratio) for r in records)
                    if v is not None]
            if vals:
                means = []
                for _ in range(N_BOOT):
                    s = [vals[random.randrange(len(vals))]
                         for _ in vals]
                    means.append(statistics.mean(s))
                means.sort()
                out["ratio_sweep"][str(ratio)][m] = {
                    "n": len(vals), "recall": statistics.mean(vals),
                    "ci": [means[int(0.025 * N_BOOT)],
                           means[int(0.975 * N_BOOT)]]}
                print(f"E5 r={ratio:4.1f} {m:10s} recall="
                      f"{statistics.mean(vals):.3f} "
                      f"CI=[{means[int(0.025*N_BOOT)]:.3f},"
                      f"{means[int(0.975*N_BOOT)]:.3f}] n={len(vals)}")

    dst = os.path.join(ROOT, "results", "local_analysis.json")
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)
    print("saved", dst)


if __name__ == "__main__":
    main()
