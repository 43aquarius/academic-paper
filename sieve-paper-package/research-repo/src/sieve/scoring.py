"""Scoring components of Sieve.

Each context sentence receives a base score that mixes question relevance
with a positional prior, plus a redundancy penalty applied during greedy
selection (implemented in :mod:`sieve.selector`).
"""
import math
from collections import Counter

from .tokens import content_tokens, idf_map, tokenize


def question_relevance(sentence_tokens: list, q_tokens: Counter,
                       idf: dict) -> float:
    """IDF-weighted coverage of question content terms by a sentence.

    The score is the sum of IDF weights of question terms covered by the
    sentence, normalized by the square root of the sentence length to avoid
    a bias toward long sentences. Terms occurring multiple times in the
    question are counted once (question-side saturation).
    """
    if not sentence_tokens or not q_tokens:
        return 0.0
    stoks = set(sentence_tokens)
    overlap = [t for t in q_tokens if t in stoks]
    if not overlap:
        return 0.0
    raw = sum(q_tokens[t] * idf.get(t, 1.0) for t in overlap)
    return raw / math.sqrt(len(sentence_tokens))


def positional_prior(index: int, n: int, floor: float = 0.35,
                     power: float = 1.5) -> float:
    """U-shaped positional weight in [floor, 1].

    ``x`` is the relative position of the sentence. The two ends of the
    context receive weight 1; the middle receives ``floor``. The shape
    encodes the primacy and recency advantage observed in long-context
    language models.
    """
    if n <= 1:
        return 1.0
    x = index / (n - 1)
    return floor + (1.0 - floor) * (abs(2.0 * x - 1.0) ** power)


def base_scores(sentences: list, question: str, alpha: float,
                floor: float, power: float) -> tuple:
    """Compute (base score, tf counter, token list) per sentence.

    ``base = alpha * relevance + (1 - alpha) * positional prior``
    """
    sent_tokens = [content_tokens(tokenize(s)) for s in sentences]
    idf = idf_map(sent_tokens)
    q_counter = Counter(content_tokens(tokenize(question)))
    scores = []
    for i, toks in enumerate(sent_tokens):
        rel = question_relevance(toks, q_counter, idf)
        pos = positional_prior(i, len(sentences), floor, power)
        scores.append(alpha * rel + (1.0 - alpha) * pos)
    counters = [Counter(toks) for toks in sent_tokens]
    return scores, counters, sent_tokens, idf
