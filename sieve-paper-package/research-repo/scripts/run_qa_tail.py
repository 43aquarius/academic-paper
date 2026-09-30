#!/usr/bin/env python3
"""Focused tail-finisher for the A0 expanded protocol.

The last N sieve-method records sit at the end of the job queue; long
worker invocations starve them (bursts get rate-limited before the
queue tail is reached). This script:

- derives the exact missing (method, record) set from the checkpoint
- fires ONE call at a time with a short per-call timeout (75 s) and a
  1-retry request (no exponential-backoff ladder burning minutes)
- on failure sleeps 20 s and moves on; loops until nothing is missing

Usage: python3 scripts/run_qa_tail.py [outer_seconds]
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))
sys.path.insert(0, os.path.join(ROOT, "eval"))

from sieve import compress, SieveConfig            # noqa: E402
import baselines as B                              # noqa: E402
from qa_metrics import exact_match, f1, contains   # noqa: E402

DATA = os.path.join(ROOT, "data")
CKPT = os.path.join(ROOT, "results", "checkpoints")
LLM = os.path.join(ROOT, "scripts", "llm_query.mjs")

SYSTEM = ("You are a precise question answering engine. Use ONLY the "
          "provided context. Reply with the shortest possible answer: an "
          "exact span copied from the context, or Yes or No for binary "
          "questions. Output nothing else.")

OUTER = float(sys.argv[1]) if len(sys.argv) > 1 else 540.0
NEED = ("full", "head", "random", "stride", "textrank", "bm25", "sieve")


def done_keys():
    done = set()
    path = os.path.join(CKPT, "qa_expanded.jsonl")
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ok") and r.get("exp") == "main":
                done.add((r["method"], r["id"]))
    return done


def append(rec):
    with open(os.path.join(CKPT, "qa_expanded.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")


def main():
    pool = json.load(open(os.path.join(DATA, "pool_qasper.json")))
    test = pool[:100]
    t0 = time.time()
    fired = ok_now = 0
    while time.time() - t0 < OUTER:
        done = done_keys()
        missing = [(m, rec) for m in NEED for rec in test
                   if (m, rec["id"]) not in done]
        if not missing:
            total = len(done)
            print(f"TAIL_DONE ok={total}")
            return
        m, rec = missing[0]
        ctx, q = rec["context"], rec["question"]
        if m == "sieve":
            text = compress(ctx, q, 4.0, SieveConfig(alpha=0.3))["text"]
        else:
            text = ctx
        user = (f"Context: {text}\n\nQuestion: {rec['question']}\n"
                f"Answer with the shortest span from the context, or "
                f"Yes/No.")
        req = json.dumps({"system": SYSTEM, "user": user,
                          "temperature": 0, "retries": 1})
        fired += 1
        try:
            out = subprocess.run(["node", LLM], input=req.encode(),
                                 capture_output=True, timeout=75)
            resp = json.loads(out.stdout.decode())
        except Exception as e:
            resp = {"ok": False, "error": str(e)[:100]}
        if resp.get("ok"):
            ok_now += 1
            pred = resp["content"]
            append({"key": f"main|{m}|r4.0|a0.3|{rec['id']}",
                    "exp": "main", "method": m, "ratio": 4.0,
                    "alpha": 0.3, "id": rec["id"],
                    "ctx_words": len(ctx.split()),
                    "comp_words": len(text.split()), "comp_ms": 0.0,
                    "ok": True, "pred": pred, "gold": rec["answers"],
                    "em": exact_match(pred, rec["answers"]),
                    "f1": f1(pred, rec["answers"]),
                    "contains": contains(pred, rec["answers"]),
                    "api_ms": None, "model": resp.get("model"),
                    "prompt_tokens": (resp.get("usage") or {}).get(
                        "prompt_tokens"),
                    "completion_tokens": (resp.get("usage") or {}).get(
                        "completion_tokens")})
            print(f"[{time.strftime('%H:%M:%S')}] OK {m} "
                  f"{rec['id'][:24]} ({ok_now} this run)", flush=True)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] fail {m} "
                  f"{rec['id'][:24]}: {resp.get('error', '?')[:60]}",
                  flush=True)
            time.sleep(20)
    print(f"TAIL_END ok={len(done_keys())} fired={fired} ok_now={ok_now}")


if __name__ == "__main__":
    main()
