"""Sieve: training-free, model-free, question-conditioned context compression.

The package exposes a single entry point, :func:`sieve.compress`, which
selects a budgeted subset of context sentences that maximizes
question-conditioned informativeness while penalizing redundancy and
accounting for positional bias in long-context language models.
"""

from .compress import compress, SieveConfig

__all__ = ["compress", "SieveConfig"]
__version__ = "1.0.0"
