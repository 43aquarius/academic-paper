#!/usr/bin/env python3
"""API experiment orchestrator for the Sieve paper.

Runs a named experiment over the sampled benchmarks, calling GLM-4-Plus via
the Node helper (scripts/llm_query.mjs) with a bounded thread pool, and
append-only JSONL checkpointing so interrupted runs resume cleanly.

Experiments
-----------
grid      : alpha grid {0.3, 0.6, 0.9} on the dev split at 4x
main      : Full / Head / Random(3 seeds) / Stride / TextRank / Sieve at 4x
ablation  : Sieve without question conditioning, without positional prior
ratio     : Sieve and Head at 2x and 8x
position  : evidence sentence placed at 5 relative positions (QASPER)

Usage: python3 scripts/run_api_experiment.py main --workers 6
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

from sieve import compress, SieveConfig                      # noqa: E402
from sieve.sentence_split import split_sentences             # noqa: E402
import baselines as B                                        # noqa: E402
from qa_metrics import exact_match, f1, contains             # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
CKPT = os.path.join(RES, "checkpoints")
os.makedirs(CKPT, exist_ok=True)

SYSTEM = ("You are a precise question answering engine. Use ONLY the "
          "provided context. Reply with the shortest possible answer: an "
          "exact span copied from the context, or Yes or No for binary "
          "questions. Output nothing else.")


def load_split():
    """Dev = first 10 of each dataset; test = 25 of each (n=50).

    The test subset of 50 is fixed by position (first 25 usable examples of
    each dataset) and kept disjoint from dev.
    """
    qs = json.load(open(os.path.join(DATA, "qasper_sample.json")))
    hp = json.load(open(os.path.join(DATA, "hotpotqa_sample.json")))
    return {"dev": qs[:10] + hp[10:20],
            "test": qs[10:35] + hp[20:45]}
    # NOTE: dev = qasper[:10] + hotpot[:10]; test = the rest


def build_context(record, method, ratio, seed, alpha):
    """Return (compressed_context, comp_ms, ctx_words, comp_words)."""
    ctx, q = record["context"], record["question"]
    ctx_words = len(ctx.split())
    t0 = time.perf_counter()
    if method == "full":
        text, comp_words = ctx, ctx_words
    elif method == "head":
        text = B.truncate_head(ctx, ratio); comp_words = len(text.split())
    elif method == "random":
        text = B.random_select(ctx, ratio, seed=seed)
        comp_words = len(text.split())
    elif method == "stride":
        text = B.stride_select(ctx, ratio); comp_words = len(text.split())
    elif method == "textrank":
        text = B.textrank_select(ctx, ratio); comp_words = len(text.split())
    elif method.startswith("sieve"):
        cfg = SieveConfig(alpha=alpha)
        if method == "sieve-noq":      # no question conditioning
            cfg.alpha = 0.0
        elif method == "sieve-nopos":  # flat positional prior
            cfg.floor = 1.0
        elif method == "sieve-nored":  # no redundancy penalty
            cfg.beta = 0.0
        out = compress(ctx, q, ratio, cfg)
        text, comp_words = out["text"], out["comp_words"]
    else:
        raise ValueError(method)
    comp_ms = (time.perf_counter() - t0) * 1000.0
    return text, comp_ms, ctx_words, comp_words


class Pacer:
    """Global request pacer: at most one request per 1/qps seconds."""

    def __init__(self, qps):
        self.interval = 1.0 / max(qps, 1e-6)
        self.lock = threading.Lock()
        self.next_time = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            if now < self.next_time:
                delay = self.next_time - now
            else:
                delay = 0.0
                self.next_time = now
            self.next_time += self.interval
        if delay > 0:
            time.sleep(delay)


def query_llm(context, question, timeout=300, pacer=None):
    if pacer is not None:
        pacer.wait()
    req = json.dumps({
        "system": SYSTEM,
        "user": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        "temperature": 0,
    })
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            ["node", os.path.join(ROOT, "scripts", "llm_query.mjs")],
            input=req.encode(), capture_output=True, timeout=timeout)
        api_ms = (time.perf_counter() - t0) * 1000.0
        out = json.loads(proc.stdout.decode() or "{}")
        if not out.get("ok"):
            return {"ok": False, "error": out.get("error", "no output"),
                    "api_ms": api_ms}
        return {"ok": True, "answer": out["content"], "api_ms": api_ms,
                "usage": out.get("usage"), "attempts": out.get("attempts", 1)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "api_ms": timeout * 1000}
    except Exception as e:
        return {"ok": False, "error": str(e),
                "api_ms": (time.perf_counter() - t0) * 1000.0}


def make_tasks(exp, alpha_default=0.6):
    split = load_split()
    test = split["test"]
    dev = split["dev"]
    tasks = []

    if exp == "grid":
        for a in (0.3, 0.6, 0.9):
            for rec in dev:
                tasks.append(dict(exp=exp, method=f"sieve-a{a}", ratio=4.0,
                                  seed=0, alpha=a, dataset_id=rec["id"],
                                  dataset="dev", record=rec))
    elif exp == "main":
        for rec in test:
            ds = "qasper" if rec["id"].startswith("qasper") else "hotpot"
            for method in ("full", "head", "stride", "textrank", "sieve"):
                tasks.append(dict(exp=exp, method=method, ratio=4.0, seed=0,
                                  alpha=alpha_default, dataset_id=rec["id"],
                                  dataset=ds, record=rec))
            for seed in (0, 1):
                tasks.append(dict(exp=exp, method="random", ratio=4.0,
                                  seed=seed, alpha=alpha_default,
                                  dataset_id=rec["id"], dataset=ds,
                                  record=rec))
    elif exp == "ablation":
        for rec in test:
            ds = "qasper" if rec["id"].startswith("qasper") else "hotpot"
            for method in ("sieve-noq", "sieve-nopos", "sieve-nred"):
                tasks.append(dict(exp=exp, method=method, ratio=4.0, seed=0,
                                  alpha=alpha_default, dataset_id=rec["id"],
                                  dataset=ds, record=rec))
    elif exp == "ratio":
        for rec in test:
            ds = "qasper" if rec["id"].startswith("qasper") else "hotpot"
            for method in ("sieve", "head"):
                for ratio in (2.0, 8.0):
                    tasks.append(dict(exp=exp, method=method, ratio=ratio,
                                      seed=0, alpha=alpha_default,
                                      dataset_id=rec["id"], dataset=ds,
                                      record=rec))
    elif exp == "position":
        qs = [r for r in test if r["id"].startswith("qasper")
              and r.get("evidence")][:20]
        for rec in qs:
            for pos in (0.0, 0.25, 0.5, 0.75, 1.0):
                tasks.append(dict(exp=exp, method=f"pos{pos}", ratio=4.0,
                                  seed=0, alpha=alpha_default,
                                  dataset_id=rec["id"], dataset="qasper",
                                  record=rec, pos=pos))
    else:
        raise ValueError(exp)
    return tasks


def position_context(record, pos, n_fillers=40):
    """Context with the gold evidence sentence placed at relative pos."""
    sents = split_sentences(record["context"])
    ev = record["evidence"]
    ev_sents = split_sentences(ev)
    anchor = ev_sents[0] if ev_sents else ev
    fillers = [s for s in sents if s != anchor][:n_fillers]
    n = len(fillers)
    slot = min(int(round(pos * n)), n)
    ctx = fillers[:slot] + [anchor] + fillers[slot:]
    return " ".join(ctx), anchor


def run_task(task, pacer=None):
    rec = task["record"]
    key = f"{task['exp']}|{task['method']}|r{task['ratio']}|s{task['seed']}|{task['dataset_id']}"
    if task["exp"] == "position":
        ctx, anchor = position_context(rec, task["pos"])
        q = rec["question"]
        comp_ms, ctx_words = 0.0, len(ctx.split())
        comp_words = ctx_words
    else:
        text, comp_ms, ctx_words, comp_words = build_context(
            rec, task["method"], task["ratio"], task["seed"], task["alpha"])
        ctx, q = text, rec["question"]
    resp = query_llm(ctx, q, pacer=pacer)
    if not resp["ok"]:
        return {"key": key, "ok": False, "error": resp["error"]}
    pred = resp["answer"]
    golds = rec["answers"]
    row = {
        "key": key,
        "ok": True,
        "exp": task["exp"],
        "method": task["method"],
        "ratio": task["ratio"],
        "seed": task["seed"],
        "dataset": task["dataset"],
        "example": task["dataset_id"],
        "ctx_words": ctx_words,
        "comp_words": comp_words,
        "comp_ms": round(comp_ms, 2),
        "api_ms": round(resp["api_ms"], 1),
        "attempts": resp.get("attempts"),
        "prompt_tokens": (resp.get("usage") or {}).get("prompt_tokens"),
        "completion_tokens": (resp.get("usage") or {}).get("completion_tokens"),
        "pred": pred[:200],
        "gold": [g[:100] for g in golds],
        "em": exact_match(pred, golds),
        "f1": f1(pred, golds),
        "contains": contains(pred, golds),
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp", choices=["grid", "main", "ablation", "ratio",
                                    "position"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--retry-failed", action="store_true",
                    help="Re-run tasks whose checkpoint row is ok=false")
    ap.add_argument("--qps", type=float, default=0.5,
                    help="Global request pacing (queries per second)")
    args = ap.parse_args()

    tasks = make_tasks(args.exp, args.alpha)
    ckpt_file = os.path.join(CKPT, f"{args.exp}.jsonl")
    done, failed_keys = set(), set()
    if os.path.exists(ckpt_file):
        for line in open(ckpt_file):
            try:
                r = json.loads(line)
                if r.get("ok"):
                    done.add(r["key"])
                else:
                    failed_keys.add(r["key"])
            except Exception:
                pass
    if args.retry_failed:
        done -= failed_keys  # allow failed rows to be retried
        # drop failed rows from the checkpoint so the file stays clean
        keep = [l for l in open(ckpt_file)
                if json.loads(l).get("ok")]
        with open(ckpt_file, "w") as f:
            f.writelines(keep)
    todo = [t for t in tasks
            if f"{t['exp']}|{t['method']}|r{t['ratio']}|s{t['seed']}|{t['dataset_id']}" not in done]
    print(f"[{args.exp}] total tasks={len(tasks)} done={len(done)} todo={len(todo)}")

    lock = threading.Lock()
    n_ok = n_fail = 0
    t_start = time.time()

    pacer = Pacer(args.qps)

    def worker(task):
        nonlocal n_ok, n_fail
        row = run_task(task, pacer)
        with lock:
            with open(ckpt_file, "a") as f:
                f.write(json.dumps(row) + "\n")
            if row.get("ok"):
                n_ok += 1
            else:
                n_fail += 1
            done_n = n_ok + n_fail
            if done_n % 20 == 0 or done_n == len(todo):
                rate = done_n / max(time.time() - t_start, 1e-6)
                eta = (len(todo) - done_n) / max(rate, 1e-6)
                print(f"[{args.exp}] {done_n}/{len(todo)} ok={n_ok} "
                      f"fail={n_fail} rate={rate:.2f}/s eta={eta/60:.1f}min",
                      flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(worker, todo))
    print(f"[{args.exp}] FINISHED ok={n_ok} fail={n_fail} "
          f"in {(time.time()-t_start)/60:.1f} min")


if __name__ == "__main__":
    main()
