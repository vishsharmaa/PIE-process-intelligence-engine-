"""Pipeline stage: persist ProcessFeature rows from ExtractionResult."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ProcessFeature
from app.schemas import ExtractionResult


def save_features(
    db: Session,
    process_id: int,
    extraction_result: ExtractionResult,
    extraction_run_id: int,
    rubric_version: str = "v1",
) -> list[ProcessFeature]:
    """
    Save ProcessFeature rows. Idempotent — deletes existing features for this
    process+version before inserting, so reruns don't create duplicates.
    """
    db.query(ProcessFeature).filter(
        ProcessFeature.process_id == process_id,
        ProcessFeature.rubric_version == rubric_version,
    ).delete()

    factor_dict = extraction_result.to_factor_dict()
    features = []
    for key, factor in factor_dict.items():
        normalized = (factor.ordinal_value - 1) / 4.0
        feat = ProcessFeature(
            process_id=process_id,
            rubric_version=rubric_version,
            feature_key=key,
            ordinal_value=factor.ordinal_value,
            normalized_value=normalized,
            rationale=factor.rationale,
            confidence=factor.confidence,
            extraction_run_id=extraction_run_id,
        )
        db.add(feat)
        features.append(feat)

    db.flush()
    return features
