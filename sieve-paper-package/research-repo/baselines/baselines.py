"""Baseline compression policies: truncation, random, striding, TextRank, BM25.

Every selector is exposed twice: ``<name>_idx`` returns the kept sentence
indices (order-preserved) under the shared word-budget convention, and
``<name>_select`` returns the compressed text. The index functions are what
the recall protocol uses, so kept-sentence recovery never relies on substring
matching.

BM25 is the classical sparse-retrieval baseline: sentences are ranked by the
BM25 score of the question against each sentence (IDF computed over the
sentences of the context itself, matching Sieve's corpus-local statistics),
packed under the same word budget, and emitted in original sentence order.
It is the strongest question-aware, model-free ranking baseline.
"""
import math
import random
from collections import Counter

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from sieve.sentence_split import split_sentences
from sieve.tokens import content_tokens, idf_map, tokenize, cosine_sparse


def _budget_words(sentences, ratio):
    total = sum(len(s.split()) for s in sentences)
    return max(1, int(total / ratio))


def _pack(order, sentences, budget):
    """Pack sentence indices greedily under the budget, emit in original order."""
    kept, used = [], 0
    for i in order:
        w = len(sentences[i].split())
        if used + w > budget and kept:
            continue
        kept.append(i)
        used += w
        if used >= budget:
            break
    return sorted(kept)


# ---------------- head ----------------
def head_idx(context: str, ratio: float):
    sentences = split_sentences(context)
    if not sentences:
        return []
    budget = _budget_words(sentences, ratio)
    kept, used = [], 0
    for i, s in enumerate(sentences):
        w = len(s.split())
        if used + w > budget and kept:
            break
        kept.append(i)
        used += w
        if used >= budget:
            break
    return kept


def truncate_head(context: str, ratio: float) -> str:
    """Keep the first ``1/ratio`` of the context (in words)."""
    words = context.split()
    n = max(1, int(len(words) / ratio))
    return " ".join(words[:n])


def truncate_tail(context: str, ratio: float) -> str:
    """Keep the last ``1/ratio`` of the context (in words)."""
    words = context.split()
    n = max(1, int(len(words) / ratio))
    return " ".join(words[-n:])


# ---------------- random ----------------
def random_idx(context: str, ratio: float, seed: int = 0):
    sentences = split_sentences(context)
    if not sentences:
        return []
    budget = _budget_words(sentences, ratio)
    rng = random.Random(seed)
    idx = list(range(len(sentences)))
    rng.shuffle(idx)
    return _pack(idx, sentences, budget)


def random_select(context: str, ratio: float, seed: int = 0) -> str:
    sentences = split_sentences(context)
    if not sentences:
        return ""
    return " ".join(sentences[i] for i in random_idx(context, ratio, seed))


# ---------------- stride ----------------
def stride_idx(context: str, ratio: float):
    sentences = split_sentences(context)
    if not sentences:
        return []
    budget = _budget_words(sentences, ratio)
    total = sum(len(s.split()) for s in sentences)
    if total <= budget:
        return list(range(len(sentences)))
    k = max(1, int(math.ceil(total / budget)))
    order = [i for i in range(len(sentences)) if i % k == 0]
    return _pack(order, sentences, budget)


def stride_select(context: str, ratio: float) -> str:
    sentences = split_sentences(context)
    if not sentences:
        return ""
    return " ".join(sentences[i] for i in stride_idx(context, ratio))


# ---------------- TextRank ----------------
def textrank_idx(context: str, ratio: float, damping: float = 0.85,
                 iters: int = 50, tol: float = 1e-6):
    """TextRank extractive summarization (question-agnostic centrality).

    Builds an IDF-weighted cosine similarity graph over sentences, runs
    power-iteration PageRank, and greedily packs the highest-ranked
    sentences under the budget, preserving original order.
    """
    sentences = split_sentences(context)
    if not sentences:
        return []
    budget = _budget_words(sentences, ratio)
    n = len(sentences)
    toks = [content_tokens(tokenize(s)) for s in sentences]
    counters = [Counter(t) for t in toks]
    idf = idf_map(toks)

    sims = {}
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_sparse(counters[i], counters[j], idf)
            if sim > 0.05:
                sims[(i, j)] = sim
                sims[(j, i)] = sim

    out_w = [sum(1 for j in range(n) if (i, j) in sims) for i in range(n)]
    scores = [1.0 / n] * n
    for _ in range(iters):
        new = []
        for i in range(n):
            acc = 0.0
            if out_w[i] > 0:
                for j in range(n):
                    if (i, j) in sims and out_w[j] > 0:
                        acc += sims[(i, j)] / out_w[j] * scores[j]
            new.append((1 - damping) / n + damping * acc)
        if max(abs(a - b) for a, b in zip(new, scores)) < tol:
            scores = new
            break
        scores = new

    order = sorted(range(n), key=lambda i: -scores[i])
    return _pack(order, sentences, budget)


def textrank_select(context: str, ratio: float) -> str:
    sentences = split_sentences(context)
    if not sentences:
        return ""
    return " ".join(sentences[i] for i in textrank_idx(context, ratio))


# ---------------- BM25 ----------------
def bm25_idx(context: str, question: str, ratio: float,
             k1: float = 1.5, b: float = 0.75):
    """BM25 sentence ranking as a budgeted selector.

    The question is the query; each sentence is a document. Term
    frequencies are computed on the same content tokens as every other
    selector, IDF is smoothed over the sentences of the context itself, and
    the top-ranked sentences are packed under the shared word budget and
    emitted in original order.
    """
    sentences = split_sentences(context)
    if not sentences:
        return []
    budget = _budget_words(sentences, ratio)
    n = len(sentences)
    sent_toks = [content_tokens(tokenize(s)) for s in sentences]
    tfs = [Counter(t) for t in sent_toks]
    lengths = [len(t) for t in sent_toks]
    avgdl = (sum(lengths) / n) if n else 0.0

    # document frequency over the context's own sentences
    df = Counter()
    for tf in tfs:
        for term in tf:
            df[term] += 1

    def idf(term):
        # Robertson-Sparck-Jones style, non-negative
        return math.log(1.0 + (n - df[term] + 0.5) / (df[term] + 0.5))

    q_terms = set(content_tokens(tokenize(question)))
    if not q_terms:
        order = list(range(n))
        return _pack(order, sentences, budget)

    scores = [0.0] * n
    for i in range(n):
        tf_i, dl_i = tfs[i], max(lengths[i], 1)
        s = 0.0
        for term in q_terms:
            f = tf_i.get(term, 0)
            if f == 0:
                continue
            denom = f + k1 * (1.0 - b + b * dl_i / max(avgdl, 1e-9))
            s += idf(term) * (f * (k1 + 1.0)) / denom
        scores[i] = s

    order = sorted(range(n), key=lambda i: -scores[i])
    return _pack(order, sentences, budget)


def bm25_select(context: str, question: str, ratio: float) -> str:
    sentences = split_sentences(context)
    if not sentences:
        return ""
    return " ".join(sentences[i] for i in bm25_idx(context, question, ratio))
