#!/usr/bin/env python3
"""Analytical projection of inference savings (simulated component).

Uses published LLaMA-2 architecture constants and standard roofline
formulas to project prefill FLOPs, KV-cache memory, prefill latency, and
token cost for full versus Sieve-compressed contexts. All assumptions are
stated explicitly in the output so they can be audited.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

# LLaMA-2 family constants (published model cards / Touvron et al. 2023)
MODELS = {
    "llama2-7b": dict(params=6.74e9, layers=32, kv_heads=32, head_dim=128),
    "llama2-13b": dict(params=13.0e9, layers=40, kv_heads=40, head_dim=128),
    "llama2-70b": dict(params=68.9e9, layers=80, kv_heads=8, head_dim=128),
}

A100_BF16_TFLOPS = 312.0  # peak
MFU = 0.40                # assumed model FLOPs utilization for prefill
BYTES_PER_ELEM = 2        # fp16/bf16
DOLLAR_PER_MTOK = {"frontier": 3.0, "budget": 0.5}  # illustrative list prices


def kv_bytes_per_token(m):
    return (2 * m["layers"] * m["kv_heads"] * m["head_dim"]
            * BYTES_PER_ELEM)


def prefill_flops(m, tokens):
    return 2.0 * m["params"] * tokens


def prefill_seconds(m, tokens):
    flops = prefill_flops(m, tokens)
    return flops / (A100_BF16_TFLOPS * 1e12 * MFU)


def main():
    rows = []
    for name, m in MODELS.items():
        for tokens in (2000, 8000, 32000, 128000):
            for ratio in (1.0, 2.0, 4.0, 8.0):
                comp_tokens = tokens / ratio
                row = {
                    "model": name,
                    "context_tokens": tokens,
                    "ratio": ratio,
                    "prefill_flops_full": prefill_flops(m, tokens),
                    "prefill_flops_comp": prefill_flops(m, comp_tokens),
                    "prefill_s_full": prefill_seconds(m, tokens),
                    "prefill_s_comp": prefill_seconds(m, comp_tokens),
                    "kv_bytes_full": kv_bytes_per_token(m) * tokens,
                    "kv_bytes_comp": kv_bytes_per_token(m) * comp_tokens,
                }
                for tag, price in DOLLAR_PER_MTOK.items():
                    row[f"cost_usd_full_{tag}"] = tokens / 1e6 * price
                    row[f"cost_usd_comp_{tag}"] = comp_tokens / 1e6 * price
                rows.append(row)

    # Perplexity-gate cost floor: one forward pass of GPT-2 (117M) over the
    # full context; LLMLingua additionally repeats this per coarse-to-fine
    # iteration. Reported for the 8k-token point.
    gpt2_params = 1.17e8
    for tokens in (2000, 8000, 32000):
        gate_flops = 2.0 * gpt2_params * tokens
        rows.append({
            "model": "gpt2-gate", "context_tokens": tokens, "ratio": 0.0,
            "prefill_flops_full": gate_flops,
            "note": "one GPT-2 forward pass over full context (LLMLingua floor)",
        })

    out = os.path.join(RES, "projection.json")
    with open(out, "w") as f:
        json.dump(rows, f, indent=1)

    # Human-readable summary at the 8k-token point
    print("=== Projection at 8k-token context, 4x compression ===")
    for name, m in MODELS.items():
        t = 8000
        kv_full = kv_bytes_per_token(m) * t / 1e9
        kv_comp = kv_bytes_per_token(m) * t / 4 / 1e9
        lat_full = prefill_seconds(m, t)
        lat_comp = prefill_seconds(m, t / 4)
        print(f"{name}: KV cache {kv_full:.2f} GB -> {kv_comp:.2f} GB; "
              f"prefill {lat_full*1000:.0f} ms -> {lat_comp*1000:.0f} ms "
              f"on 1x A100 @ MFU 0.40")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
