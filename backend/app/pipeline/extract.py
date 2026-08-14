"""Pipeline stage: call LLM to extract rubric features."""
from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import ExtractionRun, ProcessStatus
from app.schemas import ExtractionResult
from app.llm.client import extract_process
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def run_extraction(
    db: Session,
    process_id: int,
    name: str,
    raw_description: str,
    normalized_text: str,
) -> tuple[ExtractionResult, int]:
    """
    Call LLM to extract rubric features.
    Saves ExtractionRun to DB.
    Returns (ExtractionResult, extraction_run_id).
    Raises RuntimeError on failure.
    """
    result = extract_process(name, raw_description, normalized_text)

    run = ExtractionRun(
        process_id=process_id,
        model=settings.groq_model,
        prompt_version="v1",
        raw_response=result.model_dump_json(),
        created_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()

    return result, run.id
