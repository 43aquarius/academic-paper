"""Token utilities shared by scoring and selection."""
import math
import re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*")


def tokenize(text: str) -> list:
    """Lowercase word tokenizer that keeps numbers and hyphenated terms."""
    return _TOKEN.findall(text.lower())


STOPWORDS = frozenset(
    """a an the and or but if then else of to in on at by for with from as is are
    was were be been being it its this that these those there here what which who
    whom whose when where why how not no nor do does did doing have has had having
    i you he she we they them his her their our your my me us will would can could
    should shall may might must about into over under between during before after
    above below up down out off again further once all any both each few more most
    other some such only own same so than too very s t just don now d ll m o re ve
    y ain aren couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan
    shouldn wasn weren won wouldn""".split()
)


def content_tokens(tokens: list) -> list:
    """Drop stopwords and one-character tokens."""
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def idf_map(sentence_tokens: list) -> dict:
    """Self-corpus inverse document frequency over the given sentences.

    ``sentence_tokens`` is a list of token lists (one per sentence). The IDF of
    a term is log((N + 1) / (df + 1)) + 1, smoothed so that terms appearing in
    every sentence still carry a small positive weight.
    """
    n = len(sentence_tokens)
    df = Counter()
    for toks in sentence_tokens:
        for t in set(toks):
            df[t] += 1
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


def cosine_sparse(a: Counter, b: Counter, idf: dict) -> float:
    """IDF-weighted cosine similarity between two token counters."""
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    num = sum(idf.get(t, 1.0) * a[t] * b[t] for t in common)
    na = math.sqrt(sum((idf.get(t, 1.0) * c) ** 2 for t, c in a.items()))
    nb = math.sqrt(sum((idf.get(t, 1.0) * c) ** 2 for t, c in b.items()))
    if na == 0 or nb == 0:
        return 0.0
    return num / (na * nb)
