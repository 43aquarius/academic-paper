#!/usr/bin/env python3
"""Burst-mode driver for resumable checkpointed workers (429 endpoint).

The public LLM endpoint alternates between healthy windows and 429
rate-limited windows. The original driver launches one long worker
window per invocation; when rate limits hit mid-window, each in-flight
call burns up to 240 s of exponential backoff before failing. This
driver instead runs repeated short worker bursts, each gated by a
fresh probe, and sleeps 30 s between failed probes. Failed records
are retried in later bursts because the workers skip only successful
checkpoint entries.

Usage: python3 scripts/run_qa_burst.py [outer_seconds] [burst_seconds]
                             [target_ok] [worker_name] [ckpt_name]
Prints BURST_DONE when the target number of successful calls is
reached; BURST_END otherwise (resumable).
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTER = float(sys.argv[1]) if len(sys.argv) > 1 else 540.0
BURST = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
TARGET = int(sys.argv[3]) if len(sys.argv) > 3 else 760
WORKER = os.path.join(ROOT, "scripts",
                      sys.argv[4] if len(sys.argv) > 4
                      else "run_qa_expanded.py")
CKPT = os.path.join(ROOT, "results", "checkpoints",
                    sys.argv[5] if len(sys.argv) > 5
                    else "qa_expanded.jsonl")
PROBE = os.path.join(ROOT, "scripts", "probe_api.mjs")


def ok_count():
    if not os.path.exists(CKPT):
        return 0
    keys = set()
    for line in open(CKPT):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ok"):
            keys.add(r.get("key"))
    return len(keys)


def probe():
    try:
        out = subprocess.run(["node", PROBE], capture_output=True,
                             timeout=70)
        return b"PROBE_OK" in out.stdout
    except Exception:
        return False


def main():
    t0 = time.time()
    bursts = 0
    while time.time() - t0 < OUTER:
        ok = ok_count()
        if ok >= TARGET:
            print(f"BURST_DONE ok={ok}/{TARGET}")
            return
        if probe():
            remain = min(BURST, OUTER - (time.time() - t0))
            if remain < 20:
                break
            bursts += 1
            print(f"[{time.strftime('%H:%M:%S')}] burst {bursts} "
                  f"({remain:.0f}s), ok={ok}/{TARGET}", flush=True)
            try:
                subprocess.run(
                    ["python3", WORKER,
                     "--exp", "all", "--workers", "2"],
                    timeout=remain)
            except subprocess.TimeoutExpired:
                pass
        else:
            sleep = min(30.0, OUTER - (time.time() - t0))
            if sleep <= 0:
                break
            print(f"[{time.strftime('%H:%M:%S')}] probe 429; sleep "
                  f"{sleep:.0f}s (ok={ok}/{TARGET})", flush=True)
            time.sleep(sleep)
    ok = ok_count()
    print(f"BURST_END ok={ok}/{TARGET} bursts={bursts}")
    if ok >= TARGET:
        print(f"BURST_DONE ok={ok}/{TARGET}")


if __name__ == "__main__":
    main()
