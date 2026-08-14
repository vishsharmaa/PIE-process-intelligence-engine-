"""Load corpus .md files into Source + SourceChunk rows."""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

import yaml
from sqlalchemy.orm import Session

from app.models import Source, SourceChunk
from app.corpus.chunker import chunk_text
from app.corpus.embedder import embed_texts

logger = logging.getLogger(__name__)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split YAML front-matter from body text."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return meta, body
            except yaml.YAMLError:
                pass
    return {}, content


def load_corpus(db: Session, corpus_dir: str, embed: bool = True) -> int:
    """
    Load all .md files from corpus_dir.
    Upserts Source rows (by url or title), replaces chunks.
    Returns number of documents loaded.
    """
    loaded = 0
    md_files = sorted(f for f in os.listdir(corpus_dir) if f.endswith(".md"))

    for fname in md_files:
        path = os.path.join(corpus_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        meta, body = _parse_frontmatter(raw)
        title = meta.get("title", fname)
        publisher = meta.get("publisher", "")
        url = meta.get("url", "")
        year = meta.get("year")
        doc_type = meta.get("doc_type", "")
        credibility_tier = meta.get("credibility_tier", 2)

        # Upsert source
        source = db.query(Source).filter(Source.title == title).first()
        if source is None:
            source = Source(
                title=title,
                publisher=publisher,
                url=url,
                year=year,
                doc_type=doc_type,
                credibility_tier=credibility_tier,
            )
            db.add(source)
            db.flush()
        else:
            source.publisher = publisher
            source.url = url
            source.year = year
            source.doc_type = doc_type
            source.credibility_tier = credibility_tier
            # Delete old chunks
            db.query(SourceChunk).filter(SourceChunk.source_id == source.id).delete()
            db.flush()

        chunks = chunk_text(body)
        texts = [c for c in chunks if c.strip()]

        embeddings: list[Optional[list[float]]] = (
            embed_texts(texts) if embed else [None] * len(texts)
        )

        for idx, (text, emb) in enumerate(zip(texts, embeddings)):
            chunk = SourceChunk(
                source_id=source.id,
                chunk_index=idx,
                text=text,
                embedding=emb,
            )
            db.add(chunk)

        db.flush()
        loaded += 1
        logger.info(f"Loaded corpus doc: {title} ({len(texts)} chunks)")

    db.commit()
    logger.info(f"Corpus load complete: {loaded} documents.")
    return loaded


def lexical_search(db: Session, query: str, top_k: int = 5) -> list[SourceChunk]:
    """
    Simple lexical (keyword) search over source_chunk.text.
    Scores by count of query tokens found in chunk text.
    Returns top_k chunks.
    """
    tokens = set(re.sub(r"[^\w\s]", "", query.lower()).split())
    if not tokens:
        return []

    all_chunks = db.query(SourceChunk).all()
    scored = []
    for chunk in all_chunks:
        chunk_lower = chunk.text.lower()
        score = sum(1 for t in tokens if t in chunk_lower)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def embedding_search(db: Session, query_embedding: list[float], top_k: int = 5) -> list[SourceChunk]:
    """
    Vector similarity search using pgvector cosine distance.
    Falls back to empty list if embeddings not available.
    """
    from sqlalchemy import text as sa_text
    try:
        result = db.execute(
            sa_text(
                "SELECT id FROM source_chunk WHERE embedding IS NOT NULL "
                "ORDER BY embedding <=> :emb LIMIT :k"
            ),
            {"emb": str(query_embedding), "k": top_k},
        )
        ids = [row[0] for row in result]
        return db.query(SourceChunk).filter(SourceChunk.id.in_(ids)).all()
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")
        return []
