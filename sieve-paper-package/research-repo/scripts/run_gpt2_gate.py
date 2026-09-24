#!/usr/bin/env python3
"""GPT-2 perplexity-gate baseline (the neural-compressor cost floor).

Protocol (per the paper):
- Scorer: GPT-2 small (124M), dynamically quantized to int8, 2 CPU threads.
- One forward pass over the context, packed into <=1024-token windows of
  whole sentences; the question is prepended to the first window so the
  gate is question-conditioned in the LongLLMLingua sense.
- Each sentence is scored by the mean negative log-likelihood of its
  tokens (causal, conditioned on preceding text in the window).
- Selection keeps the lowest-perplexity sentences under the same word
  budget as every other method, preserving original order.
- Runs on the first 100 QASPER records of the recall pool (fixed prefix),
  measuring per-record scoring latency on the same container as every
  other timing number in the paper.

Output: results/gpt2_gate.json  (recall stats + per-record latencies)
"""
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "baselines"))

from sieve.sentence_split import split_sentences          # noqa: E402
import baselines as B                                     # noqa: E402

DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
DST = os.path.join(RES, "gpt2_gate.json")
N_RECORDS = 100
RATIO = 4.0
WINDOW = 1024

import torch                                              # noqa: E402
torch.set_num_threads(2)

MODEL = None
TOK = None


def load_model():
    global MODEL, TOK
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast
    from torch.ao.quantization import quantize_dynamic
    TOK = GPT2TokenizerFast.from_pretrained("gpt2")
    m = GPT2LMHeadModel.from_pretrained("gpt2")
    m.eval()
    try:
        m = quantize_dynamic(m, {torch.nn.Linear}, dtype=torch.qint8)
        print("gate: int8 dynamic quantization applied")
    except Exception as e:
        print(f"gate: quantization unavailable ({e}); running fp32")
    MODEL = m


def score_sentences(sentences, question):
    """Return mean-NLL score per sentence and the scoring wall-clock (s)."""
    t0 = time.perf_counter()
    q_ids = TOK.encode(question)
    # tokenize each sentence separately; concatenate with sentence spans
    spans, ids = [], []
    pos = 0
    for s in sentences:
        s_ids = TOK.encode(s)
        spans.append((pos, pos + len(s_ids)))
        ids.extend(s_ids)
        pos += len(s_ids)
    n_tok = len(ids)
    scores = [None] * len(sentences)
    # pack windows of whole sentences; question goes into the first window
    with torch.no_grad():
        i, first = 0, True
        while i < len(sentences):
            used = len(q_ids) if first else 0
            j = i
            while j < len(sentences):
                a, b = spans[j]
                if used + (b - a) > WINDOW and j > i:
                    break
                used += b - a
                j += 1
            win_ids = (q_ids if first else []) + ids[spans[i][0]:spans[j - 1][1]]
            # cap safety
            if len(win_ids) > WINDOW:
                win_ids = win_ids[:WINDOW]
            x = torch.tensor([win_ids], dtype=torch.long)
            logits = MODEL(x).logits[0]                    # [T, V]
            logp = torch.log_softmax(logits, dim=-1)
            # target token t is predicted from position t-1
            for k in range(i, j):
                a, b = spans[k]
                # positions of this sentence's tokens in the window
                off = len(q_ids) if first else 0
                a_w, b_w = a + off, b + off
                # predictable targets: positions a_w .. b_w-1 need preds from a_w-1..
                lo = max(a_w, 1)
                if b_w <= lo:
                    scores[k] = 0.0
                    continue
                tgt = torch.tensor(win_ids[lo:b_w], dtype=torch.long)
                lp = logp[lo - 1:b_w - 1].gather(1, tgt.unsqueeze(1)).squeeze(1)
                scores[k] = float(-lp.mean())
            i = j
            first = False
    dt = time.perf_counter() - t0
    return scores, dt, n_tok


def gold_indices(sents, evidence):
    ev_sents = [s.strip() for s in split_sentences(evidence)
                if len(s.split()) > 4]
    if not ev_sents:
        return set()
    idx = set()
    for es in ev_sents:
        for k, s in enumerate(sents):
            if es[:60] == s[:60]:
                idx.add(k)
    return idx


def main():
    records = json.load(open(os.path.join(DATA, "pool_qasper.json")))[:N_RECORDS]
    done = {}
    if os.path.exists(DST):
        try:
            prev = json.load(open(DST))
            done = prev.get("per_record", {})
        except Exception:
            pass
    print(f"gate: {len(records)} records, {len(done)} already done")
    load_model()

    per_record = dict(done)
    for rec in records:
        rid = rec["id"]
        if rid in per_record:
            continue
        sents = split_sentences(rec["context"])
        gold = gold_indices(sents, rec["evidence"])
        if not gold or not sents:
            continue
        scores, dt, n_tok = score_sentences(sents, rec["question"])
        # select lowest-perplexity sentences under the word budget
        budget = max(1, int(sum(len(s.split()) for s in sents) / RATIO))
        order = sorted(range(len(sents)), key=lambda k: scores[k])
        kept = B._pack(order, sents, budget)
        recall = len(gold & set(kept)) / len(gold)
        per_record[rid] = {
            "recall": recall, "score_s": dt, "n_tokens": n_tok,
            "ctx_words": len(rec["context"].split()),
            "n_sentences": len(sents),
        }
        print(f"gate {rid[:40]:42s} recall={recall:.3f} "
              f"score={dt:6.2f}s tokens={n_tok}")
        # checkpoint after every record
        vals = [v["recall"] for v in per_record.values()]
        out = {
            "n_records": len(vals),
            "recall_mean": statistics.mean(vals),
            "per_record": per_record,
        }
        json.dump(out, open(DST, "w"), indent=1)

    vals = [v["recall"] for v in per_record.values()]
    lats = [v["score_s"] for v in per_record.values()]
    words = [v["ctx_words"] for v in per_record.values()]
    order_w = sorted(range(len(words)), key=lambda i: words[i])
    med_i = order_w[len(order_w) // 2]
    p90_i = order_w[int(len(order_w) * 0.9)]
    out = {
        "n_records": len(vals),
        "recall_mean": statistics.mean(vals),
        "latency_median_s": statistics.median(lats),
        "latency_mediancontext_s": lats[med_i],
        "latency_p90context_s": lats[p90_i],
        "median_ctx_words": words[med_i],
        "per_record": per_record,
    }
    json.dump(out, open(DST, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "per_record"},
                     indent=1))


if __name__ == "__main__":
    main()
