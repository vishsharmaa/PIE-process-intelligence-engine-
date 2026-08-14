"""Pipeline stage: update process status to 'completed'."""
from __future__ import annotations

from sqlalchemy.orm import Session
from app.models import Process, ProcessStatus


def mark_completed(db: Session, process_id: int) -> None:
    """Mark process as completed."""
    proc = db.query(Process).filter(Process.id == process_id).first()
    if proc:
        proc.status = ProcessStatus.completed
        db.flush()


def mark_failed(db: Session, process_id: int) -> None:
    """Mark process as extraction_failed."""
    proc = db.query(Process).filter(Process.id == process_id).first()
    if proc:
        proc.status = ProcessStatus.extraction_failed
        db.flush()
