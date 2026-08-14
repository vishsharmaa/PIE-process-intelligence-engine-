"""Pipeline stage: compute and persist Score + ScoreFactor rows."""
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import Score, ScoreFactor, ProcessFeature
from app.scoring.engine import load_rubric, compute_score, ScoreResult


def run_scoring(
    db: Session,
    process_id: int,
    rubric_version: str = "v1",
) -> ScoreResult:
    """
    Load features from DB, compute score, persist Score + ScoreFactor rows.
    Idempotent via UNIQUE(process_id, rubric_version).
    """
    rubric = load_rubric(rubric_version)

    features_rows = (
        db.query(ProcessFeature)
        .filter(
            ProcessFeature.process_id == process_id,
            ProcessFeature.rubric_version == rubric_version,
        )
        .all()
    )

    features = {f.feature_key: f.ordinal_value for f in features_rows}
    result = compute_score(features, rubric)

    # Upsert score row
    existing = (
        db.query(Score)
        .filter(Score.process_id == process_id, Score.rubric_version == rubric_version)
        .first()
    )
    if existing:
        existing.total_score = result.total_score
        existing.band = result.band
        existing.recommendation = result.recommendation
        existing.recommendation_text = result.recommendation_text
        existing.inputs_hash = result.inputs_hash
        score_obj = existing
        # Delete old factors
        db.query(ScoreFactor).filter(ScoreFactor.score_id == score_obj.id).delete()
    else:
        score_obj = Score(
            process_id=process_id,
            rubric_version=rubric_version,
            total_score=result.total_score,
            band=result.band,
            recommendation=result.recommendation,
            recommendation_text=result.recommendation_text,
            inputs_hash=result.inputs_hash,
        )
        db.add(score_obj)
        db.flush()

    for factor in result.factors:
        sf = ScoreFactor(
            score_id=score_obj.id,
            factor_key=factor.factor_key,
            feature_value=factor.feature_value,
            weight=factor.weight,
            contribution=factor.contribution,
            direction=factor.direction,
        )
        db.add(sf)

    db.flush()

    # Verify invariant
    real_factors = [f for f in result.factors if f.factor_key != "override_cap"]
    factor_sum = round(sum(f.contribution for f in real_factors), 2)
    assert abs(factor_sum - result.total_score) < 0.01, (
        f"Score invariant violated: sum={factor_sum}, total={result.total_score}"
    )

    return result
