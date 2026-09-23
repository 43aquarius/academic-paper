#!/usr/bin/env python3
"""Chunked driver for run_qa_expanded.py.

The public LLM endpoint is intermittently rate-limited (HTTP 429). This
driver probes the endpoint once per cycle (no retries); only when the
probe succeeds does it hand the window to the resumable worker, so we
never burn minutes of exponential backoff on a blocked endpoint. Failed
records are retried on later chunks because run_qa_expanded skips only
successful checkpoint entries.

Usage: python3 scripts/run_qa_driver.py [window_seconds] [target_ok]
Prints DRIVER_DONE when the target number of successful calls is reached.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPT = os.path.join(ROOT, "results", "checkpoints", "qa_expanded.jsonl")
PROBE = os.path.join(ROOT, "scripts", "probe_api.mjs")

WINDOW = float(sys.argv[1]) if len(sys.argv) > 1 else 540.0
TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 760


def probe():
    try:
        out = subprocess.run(["node", PROBE], capture_output=True, timeout=70)
        return b"PROBE_OK" in out.stdout
    except Exception:
        return False


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


def main():
    t0 = time.time()
    launched = False
    while time.time() - t0 < WINDOW:
        ok = ok_count()
        if ok >= TARGET:
            print(f"DRIVER_DONE ok={ok}/{TARGET}")
            return
        if probe():
            remain = max(90.0, WINDOW - (time.time() - t0))
            print(f"[{time.strftime('%H:%M:%S')}] probe OK "
                  f"(ok={ok}/{TARGET}); worker window "
                  f"{remain:.0f}s", flush=True)
            try:
                subprocess.run(
                    ["python3",
                     os.path.join(ROOT, "scripts", "run_qa_expanded.py"),
                     "--exp", "all", "--workers", "2"],
                    timeout=remain)
            except subprocess.TimeoutExpired:
                pass
            launched = True
            break  # one worker window per driver invocation
        print(f"[{time.strftime('%H:%M:%S')}] probe 429; sleep 45s "
              f"(ok={ok}/{TARGET})", flush=True)
        time.sleep(45)
    ok = ok_count()
    print(f"DRIVER_CHUNK_END ok={ok}/{TARGET} launched={launched}")
    if ok >= TARGET:
        print(f"DRIVER_DONE ok={ok}/{TARGET}")


if __name__ == "__main__":
    main()
