"""
Pipeline runner — sequences all stages and writes progress to the job row.
Same code path for seeded processes and Process 101.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Job, JobStatus, Process, ProcessStatus
from app.pipeline.validate import validate, ValidationError
from app.pipeline.normalize import normalize_text, compute_hash
from app.pipeline.extract import run_extraction
from app.pipeline.features import save_features
from app.pipeline.score import run_scoring
from app.pipeline.research import run_research
from app.pipeline.persist import mark_completed, mark_failed
from app.pipeline.portfolio import recompute_portfolio

logger = logging.getLogger(__name__)


def _set_job_stage(db: Session, job_id: int, stage: str, progress: float) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.stage = stage
        job.progress = progress
        job.status = JobStatus.running
        db.commit()


def _fail_job(db: Session, job_id: int, stage: str, error: str) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.stage = stage
        job.status = JobStatus.failed
        job.error = error[:2000]
        job.finished_at = datetime.utcnow()
        db.commit()


def _complete_job(db: Session, job_id: int) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.stage = "complete"
        job.status = JobStatus.completed
        job.progress = 100.0
        job.finished_at = datetime.utcnow()
        db.commit()


def run_pipeline(process_id: int, job_id: int) -> None:
    """
    Run the full ingest pipeline for a process.
    Uses its own DB session (called from BackgroundTasks).
    """
    db: Session = SessionLocal()
    try:
        proc = db.query(Process).filter(Process.id == process_id).first()
        if proc is None:
            _fail_job(db, job_id, "start", f"Process {process_id} not found")
            return

        name = proc.name
        raw_description = proc.raw_description

        # ── validate ─────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "validate", 5.0)
        try:
            validate(name, raw_description)
        except ValidationError as e:
            _fail_job(db, job_id, "validate", str(e))
            mark_failed(db, process_id)
            db.commit()
            return

        # ── normalize ─────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "normalize", 10.0)
        normalized = normalize_text(raw_description)
        proc.normalized_text = normalized
        db.commit()

        # ── extract ───────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "extract", 20.0)
        proc.status = ProcessStatus.processing
        db.commit()
        try:
            extraction_result, extraction_run_id = run_extraction(
                db, process_id, name, raw_description, normalized
            )
            db.commit()
        except Exception as e:
            logger.error(f"Extraction failed for process {process_id}: {e}")
            _fail_job(db, job_id, "extract", str(e))
            mark_failed(db, process_id)
            db.commit()
            return

        # ── features ──────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "features", 40.0)
        try:
            save_features(db, process_id, extraction_result, extraction_run_id)
            db.commit()
        except Exception as e:
            logger.error(f"Feature save failed: {e}")
            _fail_job(db, job_id, "features", str(e))
            mark_failed(db, process_id)
            db.commit()
            return

        # ── score ─────────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "score", 55.0)
        try:
            run_scoring(db, process_id)
            db.commit()
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            _fail_job(db, job_id, "score", str(e))
            mark_failed(db, process_id)
            db.commit()
            return

        # ── research ──────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "research", 70.0)
        try:
            claims = extraction_result.claims or []
            run_research(db, process_id, claims)
            db.commit()
        except Exception as e:
            logger.warning(f"Research stage warning for process {process_id}: {e}")

        # ── persist ───────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "persist", 85.0)
        mark_completed(db, process_id)
        db.commit()

        # ── portfolio ─────────────────────────────────────────────────────
        _set_job_stage(db, job_id, "portfolio", 95.0)
        try:
            recompute_portfolio(db)
            db.commit()
        except Exception as e:
            logger.warning(f"Portfolio recompute warning: {e}")

        _complete_job(db, job_id)
        logger.info(f"Pipeline completed for process {process_id}")

    except Exception as e:
        logger.error(f"Unexpected pipeline error for process {process_id}: {e}", exc_info=True)
        try:
            _fail_job(db, job_id, "unknown", str(e))
            mark_failed(db, process_id)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()
