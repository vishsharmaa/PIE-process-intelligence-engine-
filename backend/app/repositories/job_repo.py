"""Job repository."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Job, JobStatus, Process, ProcessStatus


class JobRepo:
    @staticmethod
    def create(db: Session, process_id: int, kind: str = "ingest") -> Job:
        job = Job(kind=kind, target_process_id=process_id, status=JobStatus.queued, progress=0.0)
        db.add(job)
        db.flush()
        return job

    @staticmethod
    def get(db: Session, job_id: int) -> Optional[Job]:
        return db.query(Job).filter(Job.id == job_id).first()
