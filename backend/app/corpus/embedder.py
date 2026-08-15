"""Local sentence-transformers embedder using all-mpnet-base-v2 (768-dim)."""
from __future__ import annotations

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

_model = None


def get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model all-mpnet-base-v2…")
            _model = SentenceTransformer("all-mpnet-base-v2")
            logger.info("Embedding model loaded.")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers model: {e}. Embeddings will be None.")
            _model = None
    return _model


def embed_texts(texts: list[str]) -> list[Optional[list[float]]]:
    """
    Encode texts into 768-dim embeddings.
    Returns list of float lists; None for entries that fail.
    Falls back gracefully if model not available.
    """
    from app.config import get_settings
    if not get_settings().embed_corpus:
        return [None] * len(texts)

    model = get_model()
    if model is None:
        return [None] * len(texts)

    try:
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return [None] * len(texts)


def embed_single(text: str) -> Optional[list[float]]:
    results = embed_texts([text])
    return results[0] if results else None
