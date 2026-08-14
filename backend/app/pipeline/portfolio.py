"""Pipeline stage: recompute portfolio rankings for all completed processes."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import ProcessRank, Score, Process, ProcessStatus


def recompute_portfolio(db: Session, rubric_version: str = "v1") -> None:
    """
    Recompute all ProcessRank rows for completed processes under rubric_version.
    Ranks by total_score DESC; ties broken by process.id ASC.
    Percentile = (total - rank) / (total - 1) * 100 if total > 1 else 100.
    """
    # Fetch all completed processes with a score
    rows = (
        db.query(Score.process_id, Score.total_score)
        .join(Process, Process.id == Score.process_id)
        .filter(
            Score.rubric_version == rubric_version,
            Process.status == ProcessStatus.completed,
        )
        .order_by(Score.total_score.desc(), Score.process_id.asc())
        .all()
    )

    total = len(rows)

    # Delete existing ranks for this version
    db.query(ProcessRank).filter(ProcessRank.rubric_version == rubric_version).delete()

    now = datetime.utcnow()
    for rank_idx, (process_id, total_score) in enumerate(rows):
        rank = rank_idx + 1
        if total > 1:
            percentile = round((total - rank) / (total - 1) * 100, 1)
        else:
            percentile = 100.0

        pr = ProcessRank(
            process_id=process_id,
            rubric_version=rubric_version,
            rank=rank,
            percentile=percentile,
            computed_at=now,
        )
        db.add(pr)

    db.flush()
