#!/bin/bash
# Run one ~9-minute chunk of an API experiment (resumes from checkpoint).
# Usage: bash scripts/run_chunk.sh <exp> [alpha]
EXP=${1:-main}
ALPHA=${2:-0.3}
cd "$(dirname "$0")/.."
timeout 535 python3 scripts/run_api_experiment.py "$EXP" \
  --workers 4 --qps 0.30 --alpha "$ALPHA" 2>&1 | tail -4
python3 - <<'EOF'
import json, os
ck = "results/checkpoints/%s.jsonl" % os.environ.get("EXP", "main")
if os.path.exists(ck):
    rows = [json.loads(l) for l in open(ck)]
    ok = sum(1 for r in rows if r.get("ok"))
    print(f"progress: {ok} ok / {len(rows)} rows")
EOF
