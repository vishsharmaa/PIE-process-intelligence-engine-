"""Chunk corpus documents into ~500-token pieces with ~80-token overlap."""
from __future__ import annotations

import re


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_text(text: str, chunk_tokens: int = 500, overlap_tokens: int = 80) -> list[str]:
    """
    Split text into chunks of approximately chunk_tokens words with overlap_tokens overlap.
    Uses paragraph boundaries where possible.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current_words: list[str] = []

    for para in paragraphs:
        para_words = para.split()
        # If adding this paragraph would exceed chunk size, flush
        if current_words and _word_count(" ".join(current_words)) + len(para_words) > chunk_tokens:
            chunks.append(" ".join(current_words))
            # Keep overlap: last overlap_tokens words
            current_words = current_words[-overlap_tokens:] if len(current_words) > overlap_tokens else current_words[:]
        current_words.extend(para_words)

    if current_words:
        chunks.append(" ".join(current_words))

    # If a single chunk is too large, split it further
    result: list[str] = []
    for chunk in chunks:
        words = chunk.split()
        if len(words) <= chunk_tokens:
            result.append(chunk)
        else:
            start = 0
            while start < len(words):
                end = start + chunk_tokens
                result.append(" ".join(words[start:end]))
                start += chunk_tokens - overlap_tokens

    return [c for c in result if c.strip()]
