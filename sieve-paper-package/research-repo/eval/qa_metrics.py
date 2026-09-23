"""SQuAD-style exact match and token F1 with answer normalization."""
import re
import string
import unicodedata


def _normalize(text: str) -> str:
    """Lowercase, strip LaTeX markers, articles and punctuation."""
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("$", " ").replace("\\", " ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    # remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # remove articles
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> list:
    return _normalize(text).split()


def exact_match(pred: str, golds: list) -> int:
    p = _normalize(pred)
    return int(any(p == _normalize(g) for g in golds))


def f1(pred: str, golds: list) -> float:
    """Max token-level F1 over the gold candidates."""
    best = 0.0
    pred_t = _tokens(pred)
    for g in golds:
        gold_t = _tokens(g)
        if not gold_t or not pred_t:
            if _normalize(pred) == _normalize(g):
                best = max(best, 1.0)
            continue
        common = {}
        for t in pred_t:
            common[t] = min(pred_t.count(t), gold_t.count(t)) if t in gold_t else 0
        n_common = sum(common.values())
        if n_common == 0:
            continue
        precision = n_common / len(pred_t)
        recall = n_common / len(gold_t)
        best = max(best, 2 * precision * recall / (precision + recall))
    return best


def contains(pred: str, golds: list) -> int:
    """1 if any normalized gold appears in the normalized prediction."""
    p = _normalize(pred)
    return int(any(_normalize(g) and _normalize(g) in p for g in golds))
