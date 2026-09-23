"""Public API of Sieve."""
from dataclasses import dataclass

from .sentence_split import split_sentences
from .scoring import base_scores
from .selector import select
from .tokens import tokenize


@dataclass
class SieveConfig:
    """Hyperparameters of Sieve.

    alpha : relevance-position trade-off (1.0 = relevance only).
    beta : redundancy penalty strength.
    floor : positional weight of the context middle.
    power : sharpness of the U-shaped positional prior.
    """
    alpha: float = 0.6
    beta: float = 0.3
    floor: float = 0.35
    power: float = 1.5


def compress(context: str, question: str, ratio: float,
             cfg: SieveConfig = None, use_question: bool = True) -> dict:
    """Compress ``context`` to approximately ``1/ratio`` of its length.

    Returns a dict with the compressed text and selection diagnostics. The
    compression budget is defined in whitespace words, which tracks BPE
    tokens closely for English prose (about 1.3 tokens per word).
    """
    cfg = cfg or SieveConfig()
    sentences = split_sentences(context)
    if not sentences:
        return {"text": "", "n_sentences": 0, "kept": [],
                "orig_words": 0, "comp_words": 0}

    total_words = sum(len(s.split()) for s in sentences)
    budget = max(1, int(total_words / ratio))

    scores, counters, _, idf = base_scores(
        sentences, question if use_question else "", cfg.alpha,
        cfg.floor, cfg.power)

    kept = select(sentences, scores, counters, idf, budget, cfg.beta)
    text = " ".join(sentences[i] for i in kept)
    return {
        "text": text,
        "n_sentences": len(sentences),
        "kept": kept,
        "orig_words": total_words,
        "comp_words": len(text.split()),
    }
