"""Text normalization and error-rate helpers for ASR quality checks.

These helpers are used by the opt-in real-model tests.  They are deliberately
dependency-free so the default test suite stays lightweight.
"""

from __future__ import annotations

import unicodedata
from typing import Sequence

_SPACE_LIKE = frozenset({"P", "S", "Z", "C"})


def normalize_for_cer(text: str) -> str:
    """Lowercase and drop whitespace/punctuation/symbols for character error rate."""

    return "".join(
        char
        for char in text.lower()
        if unicodedata.category(char)[0] not in _SPACE_LIKE
    )


def normalize_for_wer(text: str) -> list[str]:
    """Lowercase and turn punctuation into spaces, then split into words."""

    characters: list[str] = []
    for char in text.lower():
        if unicodedata.category(char)[0] in _SPACE_LIKE:
            characters.append(" ")
        else:
            characters.append(char)
    return "".join(characters).split()


def edit_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    """Levenshtein distance between two token sequences."""

    if not reference:
        return len(hypothesis)

    previous = list(range(len(hypothesis) + 1))
    for row, reference_item in enumerate(reference, start=1):
        current = [row]
        for column, hypothesis_item in enumerate(hypothesis, start=1):
            substitution = 0 if reference_item == hypothesis_item else 1
            current.append(
                min(
                    previous[column] + 1,
                    current[column - 1] + 1,
                    previous[column - 1] + substitution,
                )
            )
        previous = current
    return previous[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate after punctuation/whitespace normalization."""

    reference_chars = normalize_for_cer(reference)
    hypothesis_chars = normalize_for_cer(hypothesis)
    if not reference_chars:
        return 0.0 if not hypothesis_chars else 1.0
    return edit_distance(reference_chars, hypothesis_chars) / len(reference_chars)


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate after lowercasing and punctuation normalization."""

    reference_words = normalize_for_wer(reference)
    hypothesis_words = normalize_for_wer(hypothesis)
    if not reference_words:
        return 0.0 if not hypothesis_words else 1.0
    return edit_distance(reference_words, hypothesis_words) / len(reference_words)


def cjk_ratio(text: str) -> float:
    """Share of visible characters that are CJK unified ideographs."""

    visible = normalize_for_cer(text)
    if not visible:
        return 0.0
    cjk = sum(1 for char in visible if "\u4e00" <= char <= "\u9fff")
    return cjk / len(visible)


def latin_ratio(text: str) -> float:
    """Share of visible characters that are basic Latin letters."""

    visible = normalize_for_cer(text)
    if not visible:
        return 0.0
    latin = sum(1 for char in visible if "a" <= char <= "z")
    return latin / len(visible)


__all__ = [
    "cer",
    "cjk_ratio",
    "edit_distance",
    "latin_ratio",
    "normalize_for_cer",
    "normalize_for_wer",
    "wer",
]
