#!/usr/bin/env python3
"""Download and sample benchmark data for Sieve experiments.

Datasets (real, from Hugging Face):
- QASPER: question answering over scientific papers (long contexts)
- HotpotQA (distractor setting): multi-hop QA over 10 paragraphs

Output: data/qasper_sample.json, data/hotpotqa_sample.json
Each record: {id, question, context, answers}
"""
import json
import os
import random
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

random.seed(13)

WORD_LIMIT = 6000  # cap raw context words (~8k tokens) to keep API latency sane


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ---------------- QASPER ----------------
def sample_qasper(n_dev=10, n_test=40):
    import pyarrow.parquet as pq

    local = os.path.join(DATA_DIR, "qasper-train.parquet")
    if not os.path.exists(local):
        import urllib.request
        url = ("https://huggingface.co/api/datasets/allenai/qasper/parquet/"
               "qasper/train/0.parquet")
        urllib.request.urlretrieve(url, local)
    t = pq.read_table(local).to_pylist()
    print(f"QASPER loaded: {len(t)} papers")

    def answer_of(ans):
        # Prefer extractive spans; fall back to yes/no; short free-form ok
        ev_list = ans.get("evidence") or []
        evidence = norm_ws(ev_list[0]) if ev_list else None
        if ans.get("unanswerable"):
            return None, None
        spans = ans.get("extractive_spans") or []
        if spans:
            return [norm_ws(s) for s in spans], evidence
        yn = ans.get("yes_no")
        if yn is not None:
            return [str(yn).capitalize()], evidence
        ff = norm_ws(ans.get("free_form_answer") or "")
        if 0 < len(ff.split()) <= 6:
            return [ff], evidence
        return None, None

    records = []
    for paper in t:
        ft = paper["full_text"]
        paras = []
        for plist in ft.get("paragraphs") or []:
            if isinstance(plist, str):
                paras.append(plist)
            elif isinstance(plist, list):
                paras.extend(str(x) for x in plist)
        ctx = norm_ws(" ".join(paras))
        n_words = len(ctx.split())
        if n_words < 1200:  # need genuinely long contexts
            continue
        if n_words > WORD_LIMIT:
            ctx = " ".join(ctx.split()[:WORD_LIMIT])
        qas = paper["qas"]
        questions = qas.get("question") or []
        qids = qas.get("question_id") or []
        answers = qas.get("answers") or []
        for q, qid, ansblock in zip(questions, qids, answers):
            q = norm_ws(q or "")
            if not q or len(q.split()) > 60:
                continue
            # ansblock["answer"] is a list of annotations; use the first
            annots = (ansblock or {}).get("answer") or []
            if not annots:
                continue
            ans, evidence = answer_of(annots[0] or {})
            if not ans:
                continue
            records.append({
                "id": f"qasper-{qid}",
                "question": q,
                "context": ctx,
                "answers": ans,
                "evidence": evidence,
            })
        if len(records) >= (n_dev + n_test) * 5:
            break

    random.shuffle(records)
    picked = records[: n_dev + n_test]
    out = os.path.join(DATA_DIR, "qasper_sample.json")
    with open(out, "w") as f:
        json.dump(picked, f, indent=1)
    print(f"QASPER sample: {len(picked)} -> {out}")
    print(json.dumps(picked[0], indent=1)[:500])


# ---------------- HotpotQA ----------------
def sample_hotpotqa(n_dev=10, n_test=40):
    from datasets import load_dataset

    ds = load_dataset("hotpotqa/hotpot_qa", "distractor", split="validation", trust_remote_code=True)
    print(f"HotpotQA loaded: {len(ds)} instances")

    records = []
    for inst in ds:
        q = norm_ws(inst["question"])
        ans = norm_ws(inst["answer"])
        if not q or not ans or ans.lower() in ("yes", "no"):
            continue
        titles = inst["context"]["title"]
        sents = inst["context"]["sentences"]
        paras = [norm_ws(" ".join(ss)) for t, ss in zip(titles, sents)]
        ctx = norm_ws(" ".join(paras))
        n_words = len(ctx.split())
        if n_words < 300:
            continue
        if n_words > WORD_LIMIT:
            ctx = " ".join(ctx.split()[:WORD_LIMIT])
        records.append({
            "id": f"hotpot-{inst['id']}",
            "question": q,
            "context": ctx,
            "answers": [ans],
        })
        if len(records) >= (n_dev + n_test) * 3:
            break

    random.shuffle(records)
    picked = records[: n_dev + n_test]
    out = os.path.join(DATA_DIR, "hotpotqa_sample.json")
    with open(out, "w") as f:
        json.dump(picked, f, indent=1)
    print(f"HotpotQA sample: {len(picked)} -> {out}")
    print(json.dumps(picked[0], indent=1)[:500])


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "qasper"):
        try:
            sample_qasper()
        except Exception as e:
            print(f"QASPER FAILED: {type(e).__name__}: {e}")
    if which in ("all", "hotpot"):
        try:
            sample_hotpotqa()
        except Exception as e:
            print(f"HOTPOT FAILED: {type(e).__name__}: {e}")
