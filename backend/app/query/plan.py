"""QueryPlan model and builder."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import Process


class QueryPlan(BaseModel):
    intent: str
    metric: Optional[str] = None
    filters: dict = {}
    sort: Optional[str] = None
    limit: int = 10
    target_process_id: Optional[int] = None
    rubric_version: str = "v1"


def build_plan(intent_result: dict, db: Session) -> QueryPlan:
    intent = intent_result.get("intent", "unmappable")
    limit = int(intent_result.get("limit") or 10)
    band = intent_result.get("band")
    sort = intent_result.get("sort") or ("score_desc" if intent == "rank_top" else None)
    target_id = intent_result.get("target_process_id")

    # Try to resolve process name hint to an ID
    if not target_id and intent_result.get("process_name_hint"):
        hint = intent_result["process_name_hint"]
        match = db.query(Process).filter(Process.name.ilike(f"%{hint}%")).first()
        if match:
            target_id = match.id

    filters = {}
    if band:
        filters["band"] = band

    return QueryPlan(
        intent=intent,
        filters=filters,
        sort=sort,
        limit=min(limit, 50),
        target_process_id=target_id,
    )
