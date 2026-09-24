#!/usr/bin/env python3
"""Journal-version selector-protocol experiments over the three recall pools.

Runs, per dataset pool (QASPER n=1000, HotpotQA n=300, 2Wiki n=300):
  M1  evidence recall per method at r=4 (sieve/head/random/stride/textrank/bm25)
      with bootstrap 95% CIs and paired intervals (Sieve-Head, Sieve-BM25)
  M2  ratio sweep r in {2,4,8,16} for sieve/head/textrank/random/bm25
  M3  selector ablations (QASPER only): sieve variants
  M4  position study (QASPER only): evidence placed at 5 relative positions
  M5  sensitivity (QASPER only): beta/floor/gamma grids
  M6  pool statistics (median evidence position, evidence sentences/record)
  M7  per-record recall dump at r=4 (for the recall-F1 correlation study)

No LLM calls; pure local compute. Output: results/journal_selector.json
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

from sieve import compress, SieveConfig                   # noqa: E402
from sieve.sentence_split import split_sentences          # noqa: E402
import baselines as B                                     # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
N_BOOT = 1000
BOOT_SEED = 7
RATIOS = [2.0, 4.0, 8.0, 16.0]
METHODS = ["sieve", "head", "random", "stride", "textrank", "bm25"]
CKPT = os.path.join(RES, "journal_selector.json")


def load_ckpt():
    if os.path.exists(CKPT):
        try:
            return json.load(open(CKPT))
        except Exception:
            pass
    return {}


def save_ckpt(out):
    with open(CKPT, "w") as f:
        json.dump(out, f, indent=1)
    print("checkpoint saved", CKPT)


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
    if method == "head":
        return set(B.head_idx(ctx, ratio))
    if method == "random":
        return set(B.random_idx(ctx, ratio, seed=0))
    if method == "stride":
        return set(B.stride_idx(ctx, ratio))
    if method == "textrank":
        return set(B.textrank_idx(ctx, ratio))
    if method == "bm25":
        return set(B.bm25_idx(ctx, q, ratio))
    raise ValueError(method)


def record_recall(record, method, ratio=4.0, alpha=0.3):
    sents = split_sentences(record["context"])
    gold = gold_indices(sents, record["evidence"])
    if not gold or not sents:
        return None
    kept = kept_indices(record, method, ratio, alpha)
    return len(gold & kept) / len(gold)


def boot_ci(vals, seed=BOOT_SEED):
    rng = random.Random(seed)
    means = []
    for _ in range(N_BOOT):
        s = [vals[rng.randrange(len(vals))] for _ in vals]
        means.append(statistics.mean(s))
    means.sort()
    return [means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT)]]


def paired_ci(pairs, seed=BOOT_SEED):
    """pairs: list of (a_i, b_i); CI for mean(a-b)."""
    rng = random.Random(seed)
    diffs = [a - b for a, b in pairs]
    means = []
    n = len(diffs)
    for _ in range(N_BOOT):
        s = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.mean(s))
    means.sort()
    return [means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT)]]


def method_stats(records, method, ratio=4.0):
    vals, recs = [], []
    for r in records:
        v = record_recall(r, method, ratio)
        if v is not None:
            vals.append(v)
            recs.append((r["id"], v))
    if not vals:
        return None
    out = {"n": len(vals), "recall": statistics.mean(vals),
           "ci": boot_ci(vals), "per_record": dict(recs)}
    return out


def main():
    t0 = time.time()
    pools = {}
    for name, path in [("qasper", "pool_qasper.json"),
                       ("hotpot", "pool_hotpot.json"),
                       ("2wiki", "pool_2wiki.json")]:
        p = os.path.join(DATA, path)
        if os.path.exists(p):
            pools[name] = json.load(open(p))
            print(f"pool {name}: {len(pools[name])} records")
        else:
            print(f"MISSING pool {name}; run build_pools.py first")
    out = load_ckpt()
    out["pools"] = {k: len(v) for k, v in pools.items()}

    # ---- M1: per-dataset method recall at r=4 ----
    if "methods" not in out:
        out["methods"] = {}
    for ds, records in pools.items():
        out["methods"].setdefault(ds, {})
        for m in METHODS:
            if m in out["methods"][ds]:
                continue
            st = method_stats(records, m, 4.0)
            if st:
                out["methods"][ds][m] = st
                print(f"M1 {ds:7s} {m:9s} recall={st['recall']*100:.1f} "
                      f"CI=[{st['ci'][0]*100:.1f},{st['ci'][1]*100:.1f}] "
                      f"n={st['n']}  ({time.time()-t0:.0f}s)")
        save_ckpt(out)

    # paired intervals Sieve-Head and Sieve-BM25 per dataset
    if "paired" not in out:
        out["paired"] = {}
    for ds in pools:
        out["paired"].setdefault(ds, {})
        for other in ("head", "bm25", "textrank"):
            if f"sieve-{other}" in out["paired"][ds]:
                continue
            pairs = []
            for r in pools[ds]:
                a = record_recall(r, "sieve", 4.0)
                b = record_recall(r, other, 4.0)
                if a is not None and b is not None:
                    pairs.append((a, b))
            if pairs:
                ci = paired_ci(pairs)
                mean_diff = statistics.mean(a - b for a, b in pairs)
                out["paired"][ds][f"sieve-{other}"] = {
                    "mean": mean_diff, "ci": ci, "n": len(pairs)}
                print(f"M1paired {ds:7s} sieve-{other:8s} "
                      f"d={mean_diff*100:.1f} CI=[{ci[0]*100:.1f},"
                      f"{ci[1]*100:.1f}]")
        save_ckpt(out)

    # ---- M2: ratio sweep on all datasets ----
    if "ratio_sweep" not in out:
        out["ratio_sweep"] = {}
    for ds, records in pools.items():
        out["ratio_sweep"].setdefault(ds, {})
        for ratio in RATIOS:
            out["ratio_sweep"][ds].setdefault(str(ratio), {})
            for m in ("sieve", "head", "textrank", "random", "bm25"):
                if m in out["ratio_sweep"][ds][str(ratio)]:
                    continue
                st = method_stats(records, m, ratio)
                if st:
                    out["ratio_sweep"][ds][str(ratio)][m] = {
                        "n": st["n"], "recall": st["recall"], "ci": st["ci"]}
                    print(f"M2 {ds:7s} r={ratio:4.1f} {m:9s} "
                          f"recall={st['recall']*100:.1f} "
                          f"CI=[{st['ci'][0]*100:.1f},"
                          f"{st['ci'][1]*100:.1f}]  ({time.time()-t0:.0f}s)")
            save_ckpt(out)

    # ---- M3: ablations on QASPER ----
    if "qasper" in pools and "ablations" not in out:
        out["ablations"] = {}
        for m in ("sieve", "sieve-noq", "sieve-nopos", "sieve-nored",
                  "sieve-relonly"):
            vals = [v for v in (record_recall(r, m, 4.0)
                                for r in pools["qasper"]) if v is not None]
            out["ablations"][m] = {"n": len(vals),
                                   "recall": statistics.mean(vals)}
            print(f"M3 {m:14s} recall={statistics.mean(vals)*100:.1f} "
                  f"n={len(vals)}")
        save_ckpt(out)

    # ---- M5: sensitivity on QASPER ----
    if "qasper" in pools and "sensitivity" not in out:
        out["sensitivity"] = {}
        base_cfg = {"beta": 0.3, "floor": 0.35, "gamma": 1.5}

        def recall_cfg(record, beta, floor, gamma):
            sents = split_sentences(record["context"])
            gold = gold_indices(sents, record["evidence"])
            if not gold or not sents:
                return None
            cfg = SieveConfig(alpha=0.3, beta=beta, floor=floor, power=gamma)
            o = compress(record["context"], record["question"], 4.0, cfg)
            return len(gold & set(o["kept"])) / len(gold)

        for knob, values in (("beta", (0.0, 0.3, 0.6)),
                             ("floor", (0.0, 0.35, 0.7, 1.0)),
                             ("gamma", (0.5, 1.5, 3.0))):
            out["sensitivity"][knob] = {}
            for v in values:
                kw = dict(base_cfg)
                kw[knob] = v
                vals = [x for x in (
                    recall_cfg(r, kw["beta"], kw["floor"], kw["gamma"])
                    for r in pools["qasper"]) if x is not None]
                out["sensitivity"][knob][str(v)] = {
                    "n": len(vals), "recall": statistics.mean(vals)}
                print(f"M5 {knob}={v:4.2f} recall="
                      f"{statistics.mean(vals)*100:.1f} n={len(vals)}")
        save_ckpt(out)

    # ---- M4: position study on QASPER ----
    if "qasper" in pools and "position" not in out:
        out["position"] = {}
        positions = [0.0, 0.25, 0.5, 0.75, 1.0]
        for pos in positions:
            vals = []
            for rec in pools["qasper"]:
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
                r2 = {"context": " ".join(ctx),
                      "question": rec["question"], "evidence": anchor}
                v = record_recall(r2, "sieve", 4.0)
                if v is not None:
                    vals.append(v)
            if vals:
                out["position"][str(pos)] = {"n": len(vals),
                                             "recall": statistics.mean(vals)}
                print(f"M4 pos={pos:4.2f} sieve recall="
                      f"{statistics.mean(vals)*100:.1f} n={len(vals)}")
        save_ckpt(out)

    # ---- M6: pool statistics (evidence placement + counts) ----
    out["pool_stats"] = {}
    for ds, records in pools.items():
        pos_med, evcounts = [], []
        for r in records:
            sents = split_sentences(r["context"])
            gold = gold_indices(sents, r["evidence"])
            if not gold or not sents:
                continue
            n = len(sents)
            pos_med.extend((i + 0.5) / n for i in gold)
            evcounts.append(len(gold))
        pos_med.sort()
        out["pool_stats"][ds] = {
            "n_records": len(records),
            "median_evidence_position": (pos_med[len(pos_med) // 2]
                                         if pos_med else None),
            "mean_evidence_sentences": (statistics.mean(evcounts)
                                        if evcounts else None),
            "median_ctx_words": sorted(
                len(r["context"].split()) for r in records)[len(records) // 2],
        }
        print(f"M6 {ds}: median_ev_pos="
              f"{out['pool_stats'][ds]['median_evidence_position']:.3f} "
              f"mean_ev_sents={out['pool_stats'][ds]['mean_evidence_sentences']:.1f}")

    save_ckpt(out)
    print(f"all stages complete ({time.time()-t0:.0f}s total)")


if __name__ == "__main__":
    main()
