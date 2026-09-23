"""Deterministic sentence segmentation for scientific and encyclopedic prose.

We use a regex boundary splitter rather than a statistical segmenter so that
segmentation stays model-free, reproducible, and fast (microsecond scale).
"""
import re

# A sentence boundary: period, question, or exclamation mark, optionally
# followed by closing quotes/brackets, then whitespace + capital letter or
# end of string. Abbreviations that commonly break this rule are guarded.
_BOUNDARY = re.compile(
    r"(?<=[.!?])(?:[\"')\]]+)?(?:\s+)(?=[A-Z(\[\"']|$)"
)
_ABBR = re.compile(
    r"\b(?:e\.g|i\.e|et al|vs|etc|Fig|Eq|Sec|Tab|approx|Dr|Prof|Mr|Ms|Jr|Sr|St|No|Vol)\.$",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b(?:\d|[IVXLC])\.$")


def split_sentences(text: str) -> list:
    """Split ``text`` into sentences. Returns [] for empty input."""
    text = text.strip()
    if not text:
        return []
    raw = _BOUNDARY.split(text)
    sentences = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        # Merge fragments that end in a guarded abbreviation or number.
        if sentences and (_ABBR.search(sentences[-1]) or _NUMBER.search(sentences[-1])):
            sentences[-1] = sentences[-1] + " " + s
        else:
            sentences.append(s)
    return sentences
