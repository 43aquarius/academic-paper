"""Budgeted greedy selection with a redundancy penalty (MMR-style)."""
import math

from .tokens import cosine_sparse


def select(sentences: list, scores: list, counters: list, idf: dict,
           word_budget: int, beta: float) -> list:
    """Greedy maximal-marginal-relevance selection under a word budget.

    At each step the sentence maximizing
    ``score_i - beta * max_{j in S} sim(i, j)`` is picked if it fits the
    remaining budget. Selection stops when the budget is exhausted or all
    remaining sentences overflow it. Selected sentences are returned in
    their original order to preserve discourse coherence.
    """
    n = len(sentences)
    if n == 0:
        return []
    words = [len(s.split()) for s in sentences]
    if sum(words) <= word_budget:
        return list(range(n))

    remaining = set(range(n))
    chosen = []
    used = 0
    max_sims = [0.0] * n  # running max similarity to the selected set

    while remaining:
        best_i, best_val = None, -math.inf
        for i in remaining:
            if used + words[i] > word_budget and chosen:
                # Allow one final overflow-free pass: skip sentences that
                # cannot fit unless nothing has been selected yet.
                continue
            val = scores[i] - beta * max_sims[i]
            if val > best_val:
                best_i, best_val = i, val
        if best_i is None:
            # Every remaining sentence overflows the budget; take the single
            # highest-scoring remaining sentence only if nothing fits yet.
            candidates = [i for i in remaining
                          if used + words[i] <= word_budget]
            if not candidates:
                break
            best_i = max(candidates, key=lambda i: scores[i])
        chosen.append(best_i)
        remaining.discard(best_i)
        used += words[best_i]
        for j in remaining:
            sim = cosine_sparse(counters[best_i], counters[j], idf)
            if sim > max_sims[j]:
                max_sims[j] = sim
        if used >= word_budget:
            break

    return sorted(chosen)
