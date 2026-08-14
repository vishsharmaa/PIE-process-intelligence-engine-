#!/usr/bin/env python3
"""
Seed script — loads 100 raw process descriptions and runs the real pipeline.

Usage:
    cd backend
    python scripts/seed.py                # full seed (all 100)
    python scripts/seed.py --limit 5      # seed first 5 (quick test)
    python scripts/seed.py --dry-run      # validate YAML only, no DB writes
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import yaml

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import Process, ProcessStatus, Job, JobStatus
from app.pipeline.normalize import normalize_text, compute_hash
from app.pipeline.runner import run_pipeline
from app.pipeline.portfolio import recompute_portfolio
from app.repositories.job_repo import JobRepo

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed")

SEED_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "seeds",
    "processes_100.yaml",
)


def load_seed_data(path: str) -> list[dict]:
    """Load and validate the seed YAML file."""
    if not os.path.exists(path):
        logger.error(f"Seed file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    processes = data.get("processes", [])
    if not processes:
        logger.error("No processes found in seed file")
        sys.exit(1)

    # Validate required fields
    for i, p in enumerate(processes):
        if not p.get("name"):
            logger.error(f"Process #{i+1} missing 'name'")
            sys.exit(1)
        if not p.get("raw_description") or len(p["raw_description"].strip()) < 20:
            logger.error(f"Process #{i+1} '{p.get('name')}' has insufficient description")
            sys.exit(1)

    return processes


def seed_processes(
    processes: list[dict],
    limit: int | None = None,
    dry_run: bool = False,
    delay: float = 1.0,
) -> None:
    """
    Seed processes into the database and run the real pipeline for each.

    Args:
        processes: list of process dicts from YAML
        limit: optional cap on number of processes to seed
        dry_run: if True, only validate — don't write to DB
        delay: seconds to wait between pipeline runs (rate-limit courtesy)
    """
    if limit:
        processes = processes[:limit]

    total = len(processes)
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Seeding {total} processes...")

    if dry_run:
        for i, p in enumerate(processes):
            normalized = normalize_text(p["raw_description"])
            content_hash = compute_hash(normalized)
            logger.info(
                f"  [{i+1}/{total}] {p['name'][:60]} | "
                f"dept={p.get('department', 'N/A')} | "
                f"hash={content_hash[:12]}..."
            )
        logger.info(f"Dry run complete. {total} processes validated.")
        return

    # Initialize database
    init_db()
    db = SessionLocal()

    succeeded = 0
    skipped = 0
    failed = 0

    try:
        for i, p in enumerate(processes):
            name = p["name"].strip()
            raw_description = p["raw_description"].strip()
            department = p.get("department", "").strip() or None
            industry = p.get("industry", "").strip() or None

            # Normalize and check for duplicates
            normalized = normalize_text(raw_description)
            content_hash = compute_hash(normalized)

            existing = db.query(Process).filter(Process.content_hash == content_hash).first()
            if existing:
                logger.info(f"  [{i+1}/{total}] SKIP (dup) {name[:50]} → existing id={existing.id}")
                skipped += 1
                continue

            # Create process row
            proc = Process(
                name=name,
                raw_description=raw_description,
                department=department,
                industry=industry,
                normalized_text=normalized,
                content_hash=content_hash,
                status=ProcessStatus.pending,
            )
            db.add(proc)
            db.flush()

            # Create job row
            job = JobRepo.create(db, proc.id)
            db.commit()

            logger.info(f"  [{i+1}/{total}] PIPELINE {name[:50]} (id={proc.id}, job={job.id})")

            # Run the REAL pipeline synchronously
            t0 = time.time()
            try:
                run_pipeline(proc.id, job.id)
                elapsed = time.time() - t0
                logger.info(f"    ✓ Completed in {elapsed:.1f}s")
                succeeded += 1
            except Exception as e:
                elapsed = time.time() - t0
                logger.error(f"    ✗ Failed after {elapsed:.1f}s: {e}")
                failed += 1

            # Rate-limit between pipeline runs to be courteous to Groq free tier
            if i < total - 1 and delay > 0:
                time.sleep(delay)

        # Final portfolio recomputation
        logger.info("Recomputing portfolio rankings...")
        db_final = SessionLocal()
        try:
            recompute_portfolio(db_final)
            db_final.commit()
        finally:
            db_final.close()

    finally:
        db.close()

    logger.info(
        f"\nSeed complete: {succeeded} succeeded, {skipped} skipped (dup), {failed} failed "
        f"out of {total} total."
    )
    if failed > 0:
        logger.warning(
            "Some processes failed — this may be due to Groq rate limits. "
            "Re-run the script to process remaining (duplicates will be skipped)."
        )


def main():
    parser = argparse.ArgumentParser(description="Seed the PIE database with raw process descriptions")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of processes to seed")
    parser.add_argument("--dry-run", action="store_true", help="Validate YAML without DB writes")
    parser.add_argument("--seed-file", type=str, default=SEED_FILE, help="Path to seed YAML file")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay (seconds) between pipeline runs")
    args = parser.parse_args()

    processes = load_seed_data(args.seed_file)
    logger.info(f"Loaded {len(processes)} process descriptions from {args.seed_file}")

    seed_processes(
        processes,
        limit=args.limit,
        dry_run=args.dry_run,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()
