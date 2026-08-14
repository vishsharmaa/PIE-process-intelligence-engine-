"""Process and score repositories."""
from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from app.models import Process, Score, ScoreFactor, ProcessFeature, ProcessRank, Claim, Evidence, ProcessStatus


class ProcessRepo:

    @staticmethod
    def get_by_id(db: Session, process_id: int) -> Optional[Process]:
        return db.query(Process).filter(Process.id == process_id).first()

    @staticmethod
    def get_by_hash(db: Session, content_hash: str) -> Optional[Process]:
        return db.query(Process).filter(Process.content_hash == content_hash).first()

    @staticmethod
    def list_processes(
        db: Session,
        band: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "rank",
        sort_dir: str = "asc",
        offset: int = 0,
        limit: int = 50,
        rubric_version: str = "v1",
    ) -> tuple[list[dict], int]:
        """Return (rows, total_count) with score and rank joined."""
        from sqlalchemy import func, or_

        q = (
            db.query(
                Process,
                Score.total_score,
                Score.band,
                Score.recommendation,
                ProcessRank.rank,
                ProcessRank.percentile,
            )
            .outerjoin(Score, (Score.process_id == Process.id) & (Score.rubric_version == rubric_version))
            .outerjoin(ProcessRank, (ProcessRank.process_id == Process.id) & (ProcessRank.rubric_version == rubric_version))
            .filter(Process.status == ProcessStatus.completed)
        )

        if band:
            q = q.filter(Score.band == band)
        if department:
            q = q.filter(Process.department == department)
        if search:
            q = q.filter(Process.name.ilike(f"%{search}%"))

        total = q.count()

        sort_col_map = {
            "rank": ProcessRank.rank,
            "score": Score.total_score,
            "name": Process.name,
            "created_at": Process.created_at,
        }
        sort_col = sort_col_map.get(sort_by, ProcessRank.rank)
        if sort_dir == "desc":
            q = q.order_by(desc(sort_col).nullslast())
        else:
            q = q.order_by(asc(sort_col).nullslast())

        rows = q.offset(offset).limit(limit).all()

        result = []
        for proc, total_score, band_val, rec, rank, pct in rows:
            result.append({
                "id": proc.id,
                "name": proc.name,
                "department": proc.department,
                "industry": proc.industry,
                "status": proc.status.value,
                "total_score": total_score,
                "band": band_val,
                "rank": rank,
                "percentile": pct,
                "created_at": proc.created_at,
            })
        return result, total

    @staticmethod
    def get_detail(db: Session, process_id: int, rubric_version: str = "v1") -> Optional[dict]:
        """Full process detail with features, score, factors, claims, evidence, rank."""
        proc = db.query(Process).filter(Process.id == process_id).first()
        if not proc:
            return None

        features = (
            db.query(ProcessFeature)
            .filter(
                ProcessFeature.process_id == process_id,
                ProcessFeature.rubric_version == rubric_version,
            )
            .all()
        )

        score = (
            db.query(Score)
            .filter(Score.process_id == process_id, Score.rubric_version == rubric_version)
            .first()
        )

        factors = []
        if score:
            factors = db.query(ScoreFactor).filter(ScoreFactor.score_id == score.id).all()

        claims = db.query(Claim).filter(Claim.process_id == process_id).all()
        claim_data = []
        for claim in claims:
            evidences = (
                db.query(Evidence)
                .outerjoin(Evidence.source_chunk)
                .filter(Evidence.claim_id == claim.id)
                .all()
            )
            evidence_out = []
            for ev in evidences:
                chunk_text = None
                source_title = None
                source_publisher = None
                source_url = None
                source_year = None
                if ev.source_chunk:
                    chunk_text = ev.source_chunk.text
                    if ev.source_chunk.source:
                        source_title = ev.source_chunk.source.title
                        source_publisher = ev.source_chunk.source.publisher
                        source_url = ev.source_chunk.source.url
                        source_year = ev.source_chunk.source.year
                evidence_out.append({
                    "id": ev.id,
                    "quote": ev.quote,
                    "verified": ev.verified,
                    "verification_method": ev.verification_method,
                    "source_chunk_id": ev.source_chunk_id,
                    "chunk_text": chunk_text,
                    "source_title": source_title,
                    "source_publisher": source_publisher,
                    "source_url": source_url,
                    "source_year": source_year,
                })
            claim_data.append({
                "id": claim.id,
                "claim_text": claim.claim_text,
                "claim_type": claim.claim_type,
                "supported": claim.supported,
                "evidence_items": evidence_out,
            })

        rank_obj = (
            db.query(ProcessRank)
            .filter(
                ProcessRank.process_id == process_id,
                ProcessRank.rubric_version == rubric_version,
            )
            .first()
        )

        return {
            "id": proc.id,
            "name": proc.name,
            "raw_description": proc.raw_description,
            "department": proc.department,
            "industry": proc.industry,
            "status": proc.status.value,
            "created_at": proc.created_at,
            "features": [
                {
                    "feature_key": f.feature_key,
                    "ordinal_value": f.ordinal_value,
                    "normalized_value": f.normalized_value,
                    "rationale": f.rationale,
                    "confidence": f.confidence,
                }
                for f in features
            ],
            "score": {
                "id": score.id,
                "rubric_version": score.rubric_version,
                "total_score": score.total_score,
                "band": score.band,
                "recommendation": score.recommendation,
                "recommendation_text": score.recommendation_text,
                "computed_at": score.computed_at,
                "factors": [
                    {
                        "factor_key": sf.factor_key,
                        "feature_value": sf.feature_value,
                        "weight": sf.weight,
                        "contribution": sf.contribution,
                        "direction": sf.direction,
                    }
                    for sf in factors
                ],
            } if score else None,
            "claims": claim_data,
            "rank": {
                "rank": rank_obj.rank,
                "percentile": rank_obj.percentile,
                "rubric_version": rank_obj.rubric_version,
                "computed_at": rank_obj.computed_at,
            } if rank_obj else None,
        }
