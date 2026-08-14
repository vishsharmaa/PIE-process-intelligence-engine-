"""Pipeline stage: retrieve evidence for LLM-generated claims."""
from __future__ import annotations

import logging
import time
from typing import Optional

from openai import OpenAI, RateLimitError, APITimeoutError
from sqlalchemy.orm import Session

from app.models import Claim, Evidence, SourceChunk
from app.corpus.loader import lexical_search, embedding_search
from app.corpus.verify_quote import verify_quote
from app.corpus.embedder import embed_single
from app.config import get_settings

logger = logging.getLogger(__name__)


def _ask_for_quote(
    client: OpenAI,
    model: str,
    claim: str,
    chunk_text: str,
) -> Optional[str]:
    """Ask LLM to select a verbatim quote from a chunk that supports the claim."""
    prompt = f"""Given this claim and source text, find a verbatim quote from the source text that supports the claim.
Return ONLY the exact quote as it appears in the source — no modifications, no paraphrase.
If no relevant quote exists, return exactly: NO_QUOTE

CLAIM: {claim}

SOURCE TEXT:
{chunk_text[:2000]}

Return ONLY the verbatim quote or NO_QUOTE."""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            timeout=30.0,
        )
        content = (resp.choices[0].message.content or "").strip()
        if content == "NO_QUOTE" or not content:
            return None
        return content
    except (RateLimitError, APITimeoutError):
        time.sleep(2)
        return None
    except Exception as e:
        logger.warning(f"Quote extraction failed: {e}")
        return None


def run_research(
    db: Session,
    process_id: int,
    claims: list[str],
    rubric_version: str = "v1",
) -> None:
    """
    For each claim, retrieve relevant corpus chunks and attempt to find a
    verbatim supporting quote. Save Claim + Evidence rows.
    Existing claims for this process are replaced.
    """
    settings = get_settings()
    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    # Clear existing claims for this process
    db.query(Claim).filter(Claim.process_id == process_id).delete()
    db.flush()

    for claim_text in claims:
        if not claim_text or not claim_text.strip():
            continue

        # Retrieve candidate chunks: lexical first, embedding if available
        candidate_chunks = lexical_search(db, claim_text, top_k=5)

        if len(candidate_chunks) < 3:
            # Try embedding search as a supplement
            emb = embed_single(claim_text)
            if emb:
                emb_chunks = embedding_search(db, emb, top_k=5)
                seen_ids = {c.id for c in candidate_chunks}
                for c in emb_chunks:
                    if c.id not in seen_ids:
                        candidate_chunks.append(c)

        # Create claim row
        claim_obj = Claim(
            process_id=process_id,
            claim_text=claim_text,
            claim_type="factual",
            supported=False,
        )
        db.add(claim_obj)
        db.flush()

        found_verified = False
        for chunk in candidate_chunks[:3]:  # try top-3 chunks
            quote = _ask_for_quote(client, settings.groq_model, claim_text, chunk.text)
            if quote:
                verified = verify_quote(quote, chunk.text)
                evidence = Evidence(
                    claim_id=claim_obj.id,
                    source_chunk_id=chunk.id,
                    quote=quote,
                    verified=verified,
                    verification_method="exact_match" if verified else "unverified",
                )
                db.add(evidence)
                if verified and not found_verified:
                    claim_obj.supported = True
                    found_verified = True

        if not found_verified:
            # Add an explicit unverified evidence record if no quote found
            evidence = Evidence(
                claim_id=claim_obj.id,
                source_chunk_id=None,
                quote=None,
                verified=False,
                verification_method="no_source_found",
            )
            db.add(evidence)

        db.flush()
