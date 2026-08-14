"""Verify that a quote appears verbatim in a source chunk (after normalization)."""
from __future__ import annotations

import re


def _normalize(text: str) -> str:
    """Lowercase and collapse all whitespace runs to a single space."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def verify_quote(quote: str, chunk_text: str) -> bool:
    """
    Return True if the normalized quote appears as a substring in the
    normalized chunk text. This is the sole mechanism for evidence verification —
    never paraphrase matching, never embedding similarity.
    """
    if not quote or not chunk_text:
        return False
    return _normalize(quote) in _normalize(chunk_text)
