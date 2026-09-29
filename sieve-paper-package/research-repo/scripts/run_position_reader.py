#!/usr/bin/env python3
"""B2: reader-side positional profile re-measurement (single reader).

The U-shaped position prior is currently *borrowed* from liu2023lost.
This script re-measures the reader-side profile directly: for each
QASPER record it builds a synthetic context with the gold evidence
sentence placed at one of five relative positions (same placement
logic as the M4 position study in run_journal_analysis.py, direction
reversed: the reader sees the FULL synthetic context, no selection),
asks the question under the exact A0 end-task protocol (same system
prompt, temperature 0, 96-token answer cap, same llm_query.mjs
helper), and records answer F1 as a function of evidence position.

Split discipline: records pool[110:160] -- disjoint from the A0 test
split (pool[:100]) and the alpha-grid dev split (pool[100:110]).

Checkpointed and resumable: results/checkpoints/position_reader.jsonl
Usage: python3 scripts/run_position_reader.py [--workers 2] [--limit 50]
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
sys.path.insert(0, os.path.join(ROOT, "eval"))

from sieve.sentence_split import split_sentences   # noqa: E402
from qa_metrics import exact_match, f1, contains   # noqa: E402

DATA = os.path.join(ROOT, "data")
CKPT = os.path.join(ROOT, "results", "checkpoints")
os.makedirs(CKPT, exist_ok=True)

SYSTEM = ("You are a precise question answering engine. Use ONLY the "
          "provided context. Reply with the shortest possible answer: an "
          "exact span copied from the context, or Yes or No for binary "
          "questions. Output nothing else.")

LLM = os.path.join(ROOT, "scripts", "llm_query.mjs")
POSITIONS = [0.0, 0.25, 0.5, 0.75, 1.0]
_lock = threading.Lock()


def load_records(limit):
    pool = json.load(open(os.path.join(DATA, "pool_qasper.json")))
    return pool[110:110 + limit]


def build_context(record, pos):
    """Place the first gold evidence sentence at relative position pos."""
    sents = split_sentences(record["context"])
    ev_sents = [s for s in split_sentences(record["evidence"])
                if len(s.split()) > 4]
    if not sents or not ev_sents:
        return None
    anchor = ev_sents[0]
    fillers = [s for s in sents if s != anchor][:40]
    if not fillers:
        return None
    n = len(fillers)
    slot = min(int(round(pos * n)), n)
    ctx = fillers[:slot] + [anchor] + fillers[slot:]
    return " ".join(ctx)


def ask_llm(system, user, timeout=240):
    req = json.dumps({"system": system, "user": user, "temperature": 0})
    try:
        out = subprocess.run(["node", LLM], input=req.encode(),
                             capture_output=True, timeout=timeout)
        return json.loads(out.stdout.decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_one(pos, record):
    key = f"pos|{pos}|{record['id']}"
    path = os.path.join(CKPT, "position_reader.jsonl")
    with _lock:
        if os.path.exists(path):
            for line in open(path):
                try:
                    r = json.loads(line)
                    if r.get("key") == key and r.get("ok"):
                        return None
                except Exception:
                    continue
    text = build_context(record, pos)
    if text is None:
        return None
    user = (f"Context: {text}\n\nQuestion: {record['question']}\n"
            f"Answer with the shortest span from the context, or Yes/No.")
    resp = ask_llm(SYSTEM, user)
    rec = {"key": key, "exp": "position", "pos": pos,
           "id": record["id"],
           "ctx_words": len(text.split())}
    if resp.get("ok"):
        pred = resp["content"]
        gold = record["answers"]
        rec.update({"ok": True, "pred": pred, "gold": gold,
                    "em": exact_match(pred, gold),
                    "f1": f1(pred, gold),
                    "contains": contains(pred, gold),
                    "model": resp.get("model")})
    else:
        rec.update({"ok": False, "error": resp.get("error", "unknown")})
    with _lock:
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--exp", default="all",
                    help="ignored; accepted for driver compatibility")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    records = load_records(args.limit)
    path = os.path.join(CKPT, "position_reader.jsonl")
    if args.status or True:
        if os.path.exists(path):
            done = sum(1 for l in open(path) if l.strip())
            ok = sum(1 for l in open(path)
                     if l.strip() and json.loads(l).get("ok"))
            print(f"checkpoint: {done} entries, {ok} ok")
        if args.status:
            return
    jobs = [(p, r) for p in POSITIONS for r in records]
    print(f"{len(jobs)} calls planned ({len(records)} records x "
          f"{len(POSITIONS)} positions)")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_one, *j) for j in jobs]
        done = 0
        for f in futs:
            r = f.result()
            done += 1
            if r is not None and r.get("ok"):
                print(f"[{done}/{len(jobs)}] pos={r['pos']:4.2f} "
                      f"{r['id'][:32]:34s} F1={r['f1']:.3f}")
            elif r is not None:
                print(f"[{done}/{len(jobs)}] pos={r['pos']:4.2f} "
                      f"FAILED")


if __name__ == "__main__":
    main()
