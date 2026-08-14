"""All routers in one file for speed — split later if needed."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.models import Process, ProcessStatus, Job, Score, ProcessRank, Source, Claim, Evidence, SourceChunk
from app.schemas import ProcessCreate, IngestResponse, JobOut, AskRequest, AskResponse, QueryPlanOut
from app.repositories.process_repo import ProcessRepo
from app.repositories.job_repo import JobRepo
from app.pipeline.normalize import normalize_text, compute_hash
from app.pipeline.runner import run_pipeline
from app.scoring.engine import load_rubric
from app.llm.client import classify_intent, explain_result
from app.models import QueryLog
import yaml, os, json
from datetime import datetime

# ── /health ─────────────────────────────────────────────────────────────────
meta_router = APIRouter()

@meta_router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

# ── /api/processes ───────────────────────────────────────────────────────────
proc_router = APIRouter(prefix="/api/processes", tags=["processes"])

@proc_router.get("")
def list_processes(
    band: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "rank",
    sort_dir: str = "asc",
    offset: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    rows, total = ProcessRepo.list_processes(db, band=band, department=department,
        search=search, sort_by=sort_by, sort_dir=sort_dir, offset=offset, limit=limit)
    return {"items": rows, "total": total, "offset": offset, "limit": limit}

@proc_router.get("/{process_id}")
def get_process(process_id: int, db: Session = Depends(get_db)):
    detail = ProcessRepo.get_detail(db, process_id)
    if not detail:
        raise HTTPException(404, "Process not found")
    return detail

@proc_router.post("", status_code=202)
def ingest_process(body: ProcessCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    normalized = normalize_text(body.raw_description)
    content_hash = compute_hash(normalized)
    existing = ProcessRepo.get_by_hash(db, content_hash)
    if existing:
        raise HTTPException(409, detail={
            "message": "Duplicate process — identical content already exists.",
            "existing_process_id": existing.id,
            "existing_process_name": existing.name,
        })
    proc = Process(
        name=body.name.strip(),
        raw_description=body.raw_description,
        department=body.department,
        industry=body.industry,
        external_key=body.external_key,
        normalized_text=normalized,
        content_hash=content_hash,
        status=ProcessStatus.pending,
    )
    db.add(proc)
    db.flush()
    job = JobRepo.create(db, proc.id)
    db.commit()
    background_tasks.add_task(run_pipeline, proc.id, job.id)
    return IngestResponse(job_id=job.id, process_id=proc.id, message="Pipeline started.")

@proc_router.post("/{process_id}/rescore")
def rescore_process(process_id: int, rubric_version: str = "v1", db: Session = Depends(get_db)):
    from app.pipeline.score import run_scoring
    from app.pipeline.portfolio import recompute_portfolio
    proc = ProcessRepo.get_by_id(db, process_id)
    if not proc or proc.status != ProcessStatus.completed:
        raise HTTPException(404, "Process not found or not completed")
    run_scoring(db, process_id, rubric_version)
    recompute_portfolio(db, rubric_version)
    db.commit()
    return {"message": f"Rescored under {rubric_version}"}

# ── /api/jobs ────────────────────────────────────────────────────────────────
job_router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@job_router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = JobRepo.get(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job

# ── /api/portfolio ───────────────────────────────────────────────────────────
portfolio_router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

@portfolio_router.get("/summary")
def portfolio_summary(rubric_version: str = "v1", db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = (
        db.query(Score.band, func.count(Score.id).label("count"))
        .join(Process, Process.id == Score.process_id)
        .filter(Score.rubric_version == rubric_version, Process.status == ProcessStatus.completed)
        .group_by(Score.band)
        .all()
    )
    band_counts = [{"band": r.band, "count": r.count} for r in rows]
    total = sum(r["count"] for r in band_counts)

    avg_row = db.query(func.avg(Score.total_score)).filter(Score.rubric_version == rubric_version).scalar()

    top, _ = ProcessRepo.list_processes(db, sort_by="score", sort_dir="desc", limit=5)
    bottom, _ = ProcessRepo.list_processes(db, sort_by="score", sort_dir="asc", limit=5)

    # Score distribution buckets 0-10, 10-20, ...
    buckets = []
    for i in range(0, 100, 10):
        count = (
            db.query(Score)
            .filter(Score.rubric_version == rubric_version,
                    Score.total_score >= i, Score.total_score < i + 10)
            .count()
        )
        buckets.append({"range": f"{i}-{i+10}", "count": count})

    return {
        "total": total,
        "band_counts": band_counts,
        "top_processes": top,
        "bottom_processes": bottom,
        "avg_score": round(float(avg_row), 2) if avg_row else None,
        "score_distribution": buckets,
    }

# ── /api/rubric ──────────────────────────────────────────────────────────────
rubric_router = APIRouter(prefix="/api/rubric", tags=["rubric"])

@rubric_router.get("/{version}")
def get_rubric(version: str):
    rubric_path = os.path.join(os.path.dirname(__file__), "..", "scoring", f"rubric_{version}.yaml")
    rubric_path = os.path.abspath(rubric_path)
    if not os.path.exists(rubric_path):
        raise HTTPException(404, f"Rubric version '{version}' not found")
    with open(rubric_path) as f:
        data = yaml.safe_load(f)
    return data

# ── /api/evidence ────────────────────────────────────────────────────────────
evidence_router = APIRouter(prefix="/api/evidence", tags=["evidence"])

@evidence_router.get("/{claim_id}")
def get_evidence(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")
    evidences = db.query(Evidence).filter(Evidence.claim_id == claim_id).all()
    out = []
    for ev in evidences:
        chunk = db.query(SourceChunk).filter(SourceChunk.id == ev.source_chunk_id).first() if ev.source_chunk_id else None
        source = chunk.source if chunk else None
        out.append({
            "id": ev.id,
            "quote": ev.quote,
            "verified": ev.verified,
            "verification_method": ev.verification_method,
            "chunk_text": chunk.text if chunk else None,
            "source": {"title": source.title, "publisher": source.publisher,
                        "url": source.url, "year": source.year} if source else None,
        })
    return {"claim_id": claim_id, "claim_text": claim.claim_text, "supported": claim.supported, "evidence": out}

# ── /api/compare ─────────────────────────────────────────────────────────────
compare_router = APIRouter(prefix="/api/compare", tags=["compare"])

@compare_router.post("")
def compare_processes(body: dict, db: Session = Depends(get_db)):
    ids = body.get("process_ids", [])
    if len(ids) != 2:
        raise HTTPException(400, "Provide exactly 2 process_ids")
    details = [ProcessRepo.get_detail(db, pid) for pid in ids]
    if any(d is None for d in details):
        raise HTTPException(404, "One or both processes not found")
    factor_keys = set()
    for d in details:
        if d["score"]:
            for f in d["score"]["factors"]:
                factor_keys.add(f["factor_key"])
    comparisons = []
    for key in sorted(factor_keys):
        row = {"factor_key": key, "values": {}, "contributions": {}, "direction": ""}
        for d in details:
            if d["score"]:
                for f in d["score"]["factors"]:
                    if f["factor_key"] == key:
                        row["values"][str(d["id"])] = f["feature_value"]
                        row["contributions"][str(d["id"])] = f["contribution"]
                        row["direction"] = f["direction"]
        comparisons.append(row)
    score_delta = 0.0
    if details[0]["score"] and details[1]["score"]:
        score_delta = round(details[0]["score"]["total_score"] - details[1]["score"]["total_score"], 2)
    return {"processes": [{"id": d["id"], "name": d["name"],
             "total_score": d["score"]["total_score"] if d["score"] else None,
             "band": d["score"]["band"] if d["score"] else None} for d in details],
            "factor_comparisons": comparisons, "score_delta": score_delta}

# ── /api/ask ─────────────────────────────────────────────────────────────────
ask_router = APIRouter(prefix="/api/ask", tags=["ask"])

@ask_router.post("")
def ask(body: AskRequest, db: Session = Depends(get_db)):
    from app.query.plan import build_plan
    from app.query.executors import execute_plan

    intent_result = classify_intent(body.question)
    intent = intent_result.get("intent", "unmappable")

    if intent == "unmappable":
        return {
            "question": body.question, "intent": intent,
            "query_plan": {"intent": intent, "filters": {}, "limit": 10},
            "results": None, "unmappable": True,
            "unmappable_message": (
                "I can answer: top/bottom process rankings, filter by band, "
                "explain a specific process score, portfolio statistics, or compare two processes."
            ),
        }

    plan = build_plan(intent_result, db)
    results = execute_plan(plan, db)

    prose = ""
    try:
        prose = explain_result(body.question, json.dumps(results, default=str)[:2000])
    except Exception:
        pass

    # Log query
    try:
        log = QueryLog(question=body.question, intent=intent,
                       query_plan_json=plan.model_dump(),
                       result_summary=str(results)[:500])
        db.add(log)
        db.commit()
    except Exception:
        pass

    return {
        "question": body.question,
        "intent": intent,
        "query_plan": plan.model_dump(),
        "results": results,
        "prose_explanation": prose,
        "unmappable": False,
    }
