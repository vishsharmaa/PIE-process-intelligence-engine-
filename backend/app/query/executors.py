"""Whitelisted query executors — no text-to-SQL ever."""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.models import Process, Score, ScoreFactor, ProcessRank, ProcessStatus
from app.query.plan import QueryPlan


def execute_plan(plan: QueryPlan, db: Session):
    intent = plan.intent
    if intent == "rank_top":
        return _rank_top(db, plan)
    elif intent == "filter_by_band":
        return _filter_by_band(db, plan)
    elif intent == "explain_process":
        return _explain_process(db, plan)
    elif intent == "portfolio_stats":
        return _portfolio_stats(db, plan)
    elif intent == "compare":
        return _compare(db, plan)
    elif intent == "open_research":
        return _portfolio_stats(db, plan)  # fallback
    return {"error": "unmappable"}


def _rank_top(db, plan: QueryPlan):
    band_filter = plan.filters.get("band")
    q = (
        db.query(Process.id, Process.name, Process.department, Score.total_score, Score.band, ProcessRank.rank, ProcessRank.percentile)
        .join(Score, (Score.process_id == Process.id) & (Score.rubric_version == plan.rubric_version))
        .join(ProcessRank, (ProcessRank.process_id == Process.id) & (ProcessRank.rubric_version == plan.rubric_version))
        .filter(Process.status == ProcessStatus.completed)
    )
    if band_filter:
        q = q.filter(Score.band == band_filter)
    if plan.sort == "score_asc":
        q = q.order_by(asc(Score.total_score))
    else:
        q = q.order_by(desc(Score.total_score))
    rows = q.limit(plan.limit).all()
    return [{"id": r.id, "name": r.name, "department": r.department,
             "total_score": r.total_score, "band": r.band,
             "rank": r.rank, "percentile": r.percentile} for r in rows]


def _filter_by_band(db, plan: QueryPlan):
    band = plan.filters.get("band", "Human-Led")
    q = (
        db.query(Process.id, Process.name, Process.department, Score.total_score, Score.band, ProcessRank.rank)
        .join(Score, (Score.process_id == Process.id) & (Score.rubric_version == plan.rubric_version))
        .join(ProcessRank, (ProcessRank.process_id == Process.id) & (ProcessRank.rubric_version == plan.rubric_version))
        .filter(Process.status == ProcessStatus.completed, Score.band == band)
        .order_by(desc(Score.total_score))
        .limit(plan.limit)
    )
    return [{"id": r.id, "name": r.name, "department": r.department,
             "total_score": r.total_score, "band": r.band, "rank": r.rank} for r in q.all()]


def _explain_process(db, plan: QueryPlan):
    pid = plan.target_process_id
    if not pid:
        # return top-ranked process
        pr = db.query(ProcessRank).filter(ProcessRank.rank == 1, ProcessRank.rubric_version == plan.rubric_version).first()
        pid = pr.process_id if pr else None
    if not pid:
        return {"error": "No target process found"}
    proc = db.query(Process).filter(Process.id == pid).first()
    score = db.query(Score).filter(Score.process_id == pid, Score.rubric_version == plan.rubric_version).first()
    if not score:
        return {"error": f"No score for process {pid}"}
    factors = db.query(ScoreFactor).filter(ScoreFactor.score_id == score.id).order_by(desc(ScoreFactor.contribution)).all()
    return {
        "process_id": pid,
        "name": proc.name if proc else None,
        "total_score": score.total_score,
        "band": score.band,
        "recommendation_text": score.recommendation_text,
        "factors": [{"factor_key": f.factor_key, "feature_value": f.feature_value,
                     "contribution": f.contribution, "direction": f.direction} for f in factors],
    }


def _portfolio_stats(db, plan: QueryPlan):
    total = db.query(Process).filter(Process.status == ProcessStatus.completed).count()
    band_counts = (
        db.query(Score.band, func.count(Score.id))
        .join(Process, Process.id == Score.process_id)
        .filter(Score.rubric_version == plan.rubric_version, Process.status == ProcessStatus.completed)
        .group_by(Score.band).all()
    )
    avg = db.query(func.avg(Score.total_score)).filter(Score.rubric_version == plan.rubric_version).scalar()
    return {
        "total_processes": total,
        "band_distribution": {b: c for b, c in band_counts},
        "avg_score": round(float(avg), 2) if avg else None,
    }


def _compare(db, plan: QueryPlan):
    # Needs two process IDs — fallback to top 2
    q = (
        db.query(Process.id, Process.name, Score.total_score, Score.band)
        .join(Score, (Score.process_id == Process.id) & (Score.rubric_version == plan.rubric_version))
        .filter(Process.status == ProcessStatus.completed)
        .order_by(desc(Score.total_score)).limit(2)
    )
    rows = q.all()
    return [{"id": r.id, "name": r.name, "total_score": r.total_score, "band": r.band} for r in rows]
