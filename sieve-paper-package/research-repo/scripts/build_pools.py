#!/usr/bin/env python3
"""Build the three journal-version recall pools (fixed seeds, reproducible).

Pools (per the journal protocol):
- QASPER  n=1000  train split, evidence-annotated, 6000-word cap, locatable
- HotpotQA (distractor) n=300  supporting facts locatable in flattened context
- 2WikiMultihopQA (dev) n=300  evidences locatable in flattened context

Output: data/pool_qasper.json, data/pool_hotpot.json, data/pool_2wiki.json
Each record: {id, question, context, answers, evidence}

Evidence locatability rule (same as the analysis stage): every kept evidence
sentence must prefix-match (first 60 chars) some sentence of the segmented
context, so that per-record evidence recall is well defined.
"""
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from sieve.sentence_split import split_sentences  # noqa: E402

DATA = os.path.join(ROOT, "data")
WORD_LIMIT = 6000
SEED = 20260923  # fixed, committed, reproducible


def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def evidence_locatable(context, evidence):
    """True iff every evidence sentence (>4 words) prefix-matches a context sentence."""
    ctx_sents = split_sentences(context)
    ev_sents = [s.strip() for s in split_sentences(evidence) if len(s.split()) > 4]
    if not ev_sents or not ctx_sents:
        return False
    for es in ev_sents:
        hit = any(es[:60] == s[:60] for s in ctx_sents)
        if not hit:
            return False
    return True


def cap_words(ctx):
    w = ctx.split()
    if len(w) > WORD_LIMIT:
        return " ".join(w[:WORD_LIMIT]), True
    return ctx, False


# ---------------- QASPER ----------------
def build_qasper(n=1000):
    import pyarrow.parquet as pq
    local = os.path.join(DATA, "qasper-train.parquet")
    if not os.path.exists(local):
        import urllib.request
        url = ("https://huggingface.co/api/datasets/allenai/qasper/parquet/"
               "qasper/train/0.parquet")
        urllib.request.urlretrieve(url, local)
    t = pq.read_table(local).to_pylist()
    print(f"QASPER loaded: {len(t)} papers")

    def answer_of(ans):
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
        if n_words < 1200:
            continue
        ctx, _ = cap_words(ctx)
        qas = paper["qas"]
        for q, qid, ansblock in zip(qas.get("question") or [],
                                     qas.get("question_id") or [],
                                     qas.get("answers") or []):
            q = norm_ws(q or "")
            if not q or len(q.split()) > 60:
                continue
            annots = (ansblock or {}).get("answer") or []
            if not annots:
                continue
            ans, evidence = answer_of(annots[0] or {})
            if not ans or not evidence:
                continue
            records.append({
                "id": f"qasper-{qid}", "question": q, "context": ctx,
                "answers": ans, "evidence": evidence,
            })
    print(f"QASPER candidates with evidence: {len(records)}")

    rng = random.Random(SEED)
    rng.shuffle(records)
    pool = []
    for r in records:
        if len(pool) >= n:
            break
        if evidence_locatable(r["context"], r["evidence"]):
            pool.append(r)
    out = os.path.join(DATA, "pool_qasper.json")
    json.dump(pool, open(out, "w"))
    med = sorted(len(r["context"].split()) for r in pool)[len(pool) // 2]
    p90 = sorted(len(r["context"].split()) for r in pool)[int(len(pool) * 0.9)]
    print(f"QASPER pool: {len(pool)} records (median {med} words, p90 {p90}) -> {out}")
    return pool


# ---------------- HotpotQA (distractor) ----------------
def build_hotpot(n=300):
    import urllib.request
    import pyarrow.parquet as pq
    local = os.path.join(DATA, "hotpot-distractor-dev.parquet")
    if not os.path.exists(local):
        url = ("https://huggingface.co/api/datasets/hotpotqa/hotpot_qa/"
               "parquet/distractor/validation/0.parquet")
        print("downloading hotpot distractor validation parquet ...")
        urllib.request.urlretrieve(url, local)
    t = pq.read_table(local).to_pylist()
    print(f"HotpotQA loaded: {len(t)} instances")

    records = []
    for inst in t:
        q = norm_ws(inst["question"])
        ans = norm_ws(inst["answer"])
        if not q or not ans or ans.lower() in ("yes", "no"):
            continue
        titles = inst["context"]["title"]
        sents = inst["context"]["sentences"]
        sf_titles = list(inst["supporting_facts"]["title"])
        sf_sids = list(inst["supporting_facts"]["sent_id"])
        title_to_par = {t: i for i, t in enumerate(titles)}
        ev_pairs = []
        for tt, sid in zip(sf_titles, sf_sids):
            if tt in title_to_par:
                pi = title_to_par[tt]
                ss = sents[pi]
                if sid < len(ss):
                    ev_pairs.append((pi, sid, norm_ws(ss[sid])))
        if not ev_pairs:
            continue
        paras = [norm_ws(" ".join(ss)) for tt, ss in zip(titles, sents)]
        ctx = norm_ws(" ".join(paras))
        if len(ctx.split()) < 300:
            continue
        ctx, _ = cap_words(ctx)
        evidence = norm_ws(" ".join(e[2] for e in ev_pairs))
        records.append({
            "id": f"hotpot-{inst['id']}", "question": q, "context": ctx,
            "answers": [ans], "evidence": evidence,
        })
        if len(records) >= n * 6:
            break
    print(f"HotpotQA candidates: {len(records)}")
    rng = random.Random(SEED)
    rng.shuffle(records)
    pool = []
    for r in records:
        if len(pool) >= n:
            break
        if evidence_locatable(r["context"], r["evidence"]):
            pool.append(r)
    out = os.path.join(DATA, "pool_hotpot.json")
    json.dump(pool, open(out, "w"))
    med = sorted(len(r["context"].split()) for r in pool)[len(pool) // 2]
    print(f"HotpotQA pool: {len(pool)} records (median {med} words) -> {out}")
    return pool


# ---------------- 2WikiMultihopQA (dev) ----------------
def build_2wiki(n=300):
    import urllib.request
    import pyarrow.parquet as pq
    local = os.path.join(DATA, "2wiki-dev.parquet")
    if not os.path.exists(local):
        url = ("https://huggingface.co/api/datasets/framolfese/"
               "2WikiMultihopQA/parquet/default/validation/0.parquet")
        print("downloading 2Wiki validation parquet ...")
        urllib.request.urlretrieve(url, local)
    t = pq.read_table(local).to_pylist()
    print(f"2Wiki loaded: {len(t)} instances")
    print("columns:", list(t[0].keys()))

    records = []
    for inst in t:
        q = norm_ws(inst.get("question") or "")
        ans = norm_ws(str(inst.get("answer") or ""))
        if not q or not ans or ans.lower() in ("yes", "no"):
            continue
        titles = inst["context"]["title"]
        sents = inst["context"]["sentences"]
        sf = inst.get("supporting_facts") or {}
        sf_titles = list(sf.get("title") or [])
        sf_sids = list(sf.get("sent_id") or [])
        title_to_par = {tt: i for i, tt in enumerate(titles)}
        ev_sents = []
        for tt, sid in zip(sf_titles, sf_sids):
            if tt in title_to_par:
                pi = title_to_par[tt]
                ss = sents[pi]
                if sid < len(ss):
                    ev_sents.append(norm_ws(ss[sid]))
        if not ev_sents:
            continue
        paras = [norm_ws(" ".join(ss)) for tt, ss in zip(titles, sents)]
        ctx = norm_ws(" ".join(paras))
        if len(ctx.split()) < 300:
            continue
        ctx, _ = cap_words(ctx)
        evidence = norm_ws(" ".join(dict.fromkeys(ev_sents)))
        rid = inst.get("_id") or inst.get("id") or f"2wiki-{len(records)}"
        records.append({
            "id": f"2wiki-{rid}", "question": q, "context": ctx,
            "answers": [ans], "evidence": evidence,
        })
        if len(records) >= n * 6:
            break
    print(f"2Wiki candidates: {len(records)}")
    rng = random.Random(SEED)
    rng.shuffle(records)
    pool = []
    for r in records:
        if len(pool) >= n:
            break
        if evidence_locatable(r["context"], r["evidence"]):
            pool.append(r)
    out = os.path.join(DATA, "pool_2wiki.json")
    json.dump(pool, open(out, "w"))
    med = sorted(len(r["context"].split()) for r in pool)[len(pool) // 2]
    print(f"2Wiki pool: {len(pool)} records (median {med} words) -> {out}")
    return pool


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "qasper"):
        try:
            build_qasper()
        except Exception as e:
            print(f"QASPER FAILED: {type(e).__name__}: {e}")
    if which in ("all", "hotpot"):
        try:
            build_hotpot()
        except Exception as e:
            print(f"HOTPOT FAILED: {type(e).__name__}: {e}")
    if which in ("all", "2wiki"):
        try:
            build_2wiki()
        except Exception as e:
            print(f"2WIKI FAILED: {type(e).__name__}: {e}")
