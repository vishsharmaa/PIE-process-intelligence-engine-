"""Pipeline stage: normalize process text and compute content_hash."""
from __future__ import annotations

import hashlib
import re


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace and punctuation runs."""
    text = text.lower()
    # collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)
    # collapse multiple punctuation (keep single)
    text = re.sub(r"[^\w\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compute_hash(normalized_text: str) -> str:
    """SHA-256 hash of normalized text."""
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
