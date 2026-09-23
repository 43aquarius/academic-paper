"""Baseline compression policies: truncation, random, striding, TextRank."""
import math
import random
import re
from collections import Counter

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from sieve.sentence_split import split_sentences
from sieve.tokens import content_tokens, idf_map, tokenize, cosine_sparse


def _budget_words(sentences, ratio):
    total = sum(len(s.split()) for s in sentences)
    return max(1, int(total / ratio))


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


def random_select(context: str, ratio: float, seed: int = 0) -> str:
    """Random sentence subset under the budget, order preserved."""
    rng = random.Random(seed)
    sentences = split_sentences(context)
    if not sentences:
        return ""
    budget = _budget_words(sentences, ratio)
    idx = list(range(len(sentences)))
    rng.shuffle(idx)
    kept, used = [], 0
    for i in idx:
        w = len(sentences[i].split())
        if used + w > budget and kept:
            continue
        kept.append(i)
        used += w
        if used >= budget:
            break
    return " ".join(sentences[i] for i in sorted(kept))


def stride_select(context: str, ratio: float) -> str:
    """Uniform striding: keep every k-th sentence, k ~ ratio."""
    sentences = split_sentences(context)
    if not sentences:
        return ""
    budget = _budget_words(sentences, ratio)
    total = sum(len(s.split()) for s in sentences)
    if total <= budget:
        return context
    k = max(1, int(math.ceil(total / budget)))
    # Walk sentence by sentence, keeping one sentence per k-sentence block.
    kept, used, block = [], 0, 0
    for i, s in enumerate(sentences):
        if i % k == 0:
            w = len(s.split())
            if used + w > budget and kept:
                break
            kept.append(s)
            used += w
            if used >= budget:
                break
    return " ".join(kept)


def textrank_select(context: str, ratio: float, damping: float = 0.85,
                    iters: int = 50, tol: float = 1e-6) -> str:
    """TextRank extractive summarization (question-agnostic centrality).

    Builds an IDF-weighted cosine similarity graph over sentences, runs
    power-iteration PageRank, and greedily packs the highest-ranked
    sentences under the budget, preserving original order.
    """
    sentences = split_sentences(context)
    if not sentences:
        return ""
    budget = _budget_words(sentences, ratio)
    n = len(sentences)
    toks = [content_tokens(tokenize(s)) for s in sentences]
    counters = [Counter(t) for t in toks]
    idf = idf_map(toks)

    # Sparse similarity graph (thresholded to keep the graph readable).
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
    kept, used = [], 0
    for i in order:
        w = len(sentences[i].split())
        if used + w > budget and kept:
            continue
        kept.append(i)
        used += w
        if used >= budget:
            break
    return " ".join(sentences[i] for i in sorted(kept))
