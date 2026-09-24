#!/usr/bin/env python3
"""Expanded end-task QA evaluation (n=100) at the 4x operating point.

Reader: the production LLM served through the same public API helper as
the conference-version experiments (scripts/llm_query.mjs, temperature 0,
max 96 answer tokens, shortest-span instruction).

Splits (fixed, disjoint):
- test  : the first 100 QASPER records of the rebuilt recall pool
          (the same 100 records the GPT-2 gate ran on, so per-record
          recall and F1 join exactly for the correlation study)
- dev   : 10 further QASPER records + 10 HotpotQA records (alpha grid)

Methods at r=4: full / head / random / stride / textrank / bm25 / sieve

Checkpointed and resumable: results/checkpoints/qa_expanded.jsonl
Usage: python3 scripts/run_qa_expanded.py [--workers 2] [--alpha 0.3]
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))
sys.path.insert(0, os.path.join(ROOT, "eval"))

from sieve import compress, SieveConfig            # noqa: E402
import baselines as B                              # noqa: E402
from qa_metrics import exact_match, f1, contains   # noqa: E402

DATA = os.path.join(ROOT, "data")
CKPT = os.path.join(ROOT, "results", "checkpoints")
os.makedirs(CKPT, exist_ok=True)

SYSTEM = ("You are a precise question answering engine. Use ONLY the "
          "provided context. Reply with the shortest possible answer: an "
          "exact span copied from the context, or Yes or No for binary "
          "questions. Output nothing else.")

LLM = os.path.join(ROOT, "scripts", "llm_query.mjs")
_lock = threading.Lock()


def load_splits():
    pool = json.load(open(os.path.join(DATA, "pool_qasper.json")))
    hp = json.load(open(os.path.join(DATA, "pool_hotpot.json")))
    return {"test": pool[:100],
            "dev_q": pool[100:110],
            "dev_h": hp[:10]}


def build_context(record, method, ratio=4.0, alpha=0.3, seed=0):
    ctx, q = record["context"], record["question"]
    t0 = time.perf_counter()
    if method == "full":
        text = ctx
    elif method == "head":
        text = B.truncate_head(ctx, ratio)
    elif method == "random":
        text = B.random_select(ctx, ratio, seed=seed)
    elif method == "stride":
        text = B.stride_select(ctx, ratio)
    elif method == "textrank":
        text = B.textrank_select(ctx, ratio)
    elif method == "bm25":
        text = B.bm25_select(ctx, q, ratio)
    elif method == "sieve":
        text = compress(ctx, q, ratio, SieveConfig(alpha=alpha))["text"]
    else:
        raise ValueError(method)
    return text, (time.perf_counter() - t0) * 1000.0


def ask_llm(system, user, timeout=240):
    req = json.dumps({"system": system, "user": user, "temperature": 0})
    try:
        out = subprocess.run(["node", LLM], input=req.encode(),
                             capture_output=True, timeout=timeout)
        return json.loads(out.stdout.decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_one(exp, method, record, ratio=4.0, alpha=0.3, seed=0):
    key = f"{exp}|{method}|r{ratio}|a{alpha}|{record['id']}"
    path = os.path.join(CKPT, "qa_expanded.jsonl")
    with _lock:
        if os.path.exists(path):
            for line in open(path):
                try:
                    r = json.loads(line)
                    if r.get("key") == key and r.get("ok"):
                        return None  # already done successfully
                except Exception:
                    continue
    text, comp_ms = build_context(record, method, ratio, alpha, seed)
    user = (f"Context: {text}\n\nQuestion: {record['question']}\n"
            f"Answer with the shortest span from the context, or Yes/No.")
    resp = ask_llm(SYSTEM, user)
    rec = {"key": key, "exp": exp, "method": method, "ratio": ratio,
           "alpha": alpha, "id": record["id"],
           "ctx_words": len(record["context"].split()),
           "comp_words": len(text.split()), "comp_ms": round(comp_ms, 2)}
    if resp.get("ok"):
        pred = resp["content"]
        gold = record["answers"]
        rec.update({"ok": True, "pred": pred, "gold": gold,
                    "em": exact_match(pred, gold),
                    "f1": f1(pred, gold),
                    "contains": contains(pred, gold),
                    "api_ms": None, "model": resp.get("model"),
                    "prompt_tokens": (resp.get("usage") or {}).get(
                        "prompt_tokens"),
                    "completion_tokens": (resp.get("usage") or {}).get(
                        "completion_tokens")})
    else:
        rec.update({"ok": False, "error": resp.get("error", "unknown")})
    with _lock:
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--alpha", type=float, default=0.3)
    ap.add_argument("--exp", default="all",
                    choices=["all", "grid", "main", "status"])
    args = ap.parse_args()

    splits = load_splits()
    jobs = []
    if args.exp in ("all", "status"):
        path = os.path.join(CKPT, "qa_expanded.jsonl")
        if os.path.exists(path):
            done = sum(1 for l in open(path) if l.strip())
            ok = sum(1 for l in open(path)
                     if l.strip() and json.loads(l).get("ok"))
            print(f"checkpoint: {done} entries, {ok} ok")
        if args.exp == "status":
            return
    if args.exp in ("all", "grid"):
        for a in (0.3, 0.6, 0.9):
            for rec in splits["dev_q"] + splits["dev_h"]:
                jobs.append(("grid", "sieve", rec, 4.0, a, 0))
    if args.exp in ("all", "main"):
        for m in ("full", "head", "random", "stride", "textrank",
                  "bm25", "sieve"):
            for rec in splits["test"]:
                jobs.append(("main", m, rec, 4.0, args.alpha, 0))

    print(f"{len(jobs)} calls planned")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_one, *j) for j in jobs]
        done = 0
        for f in futs:
            r = f.result()
            done += 1
            if r is not None and r.get("ok"):
                print(f"[{done}/{len(jobs)}] {r['method']:9s} "
                      f"{r['id'][:32]:34s} F1={r['f1']:.3f}")
            elif r is not None:
                print(f"[{done}/{len(jobs)}] {r['method']:9s} FAILED")


if __name__ == "__main__":
    main()
