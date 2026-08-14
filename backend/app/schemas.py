from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


# ── Process ──────────────────────────────────────────────────────────────────

class ProcessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    raw_description: str = Field(..., min_length=10)
    department: Optional[str] = None
    industry: Optional[str] = None
    external_key: Optional[str] = None


class ProcessSummary(BaseModel):
    id: int
    name: str
    department: Optional[str]
    industry: Optional[str]
    status: str
    total_score: Optional[float] = None
    band: Optional[str] = None
    rank: Optional[int] = None
    percentile: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FactorOut(BaseModel):
    factor_key: str
    feature_value: float
    weight: float
    contribution: float
    direction: str

    model_config = {"from_attributes": True}


class ScoreOut(BaseModel):
    id: int
    rubric_version: str
    total_score: float
    band: str
    recommendation: str
    recommendation_text: str
    computed_at: datetime
    factors: List[FactorOut] = []

    model_config = {"from_attributes": True}


class FeatureOut(BaseModel):
    feature_key: str
    ordinal_value: int
    normalized_value: float
    rationale: Optional[str]
    confidence: Optional[float]

    model_config = {"from_attributes": True}


class EvidenceOut(BaseModel):
    id: int
    quote: Optional[str]
    verified: bool
    verification_method: Optional[str]
    source_chunk_id: Optional[int]
    chunk_text: Optional[str] = None
    source_title: Optional[str] = None
    source_publisher: Optional[str] = None
    source_url: Optional[str] = None
    source_year: Optional[int] = None

    model_config = {"from_attributes": True}


class ClaimOut(BaseModel):
    id: int
    claim_text: str
    claim_type: Optional[str]
    supported: bool
    evidence_items: List[EvidenceOut] = []

    model_config = {"from_attributes": True}


class RankOut(BaseModel):
    rank: int
    percentile: float
    rubric_version: str
    computed_at: datetime

    model_config = {"from_attributes": True}


class ProcessDetail(BaseModel):
    id: int
    name: str
    raw_description: str
    department: Optional[str]
    industry: Optional[str]
    status: str
    created_at: datetime
    features: List[FeatureOut] = []
    score: Optional[ScoreOut] = None
    claims: List[ClaimOut] = []
    rank: Optional[RankOut] = None

    model_config = {"from_attributes": True}


# ── Job ───────────────────────────────────────────────────────────────────────

class JobOut(BaseModel):
    id: int
    kind: str
    target_process_id: Optional[int]
    status: str
    stage: Optional[str]
    progress: float
    error: Optional[str]
    created_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    job_id: int
    process_id: int
    message: str


# ── Portfolio ─────────────────────────────────────────────────────────────────

class BandCount(BaseModel):
    band: str
    count: int


class PortfolioSummary(BaseModel):
    total: int
    band_counts: List[BandCount]
    top_processes: List[ProcessSummary]
    bottom_processes: List[ProcessSummary]
    avg_score: Optional[float]
    score_distribution: List[dict]


# ── Ask / NL Query ────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class QueryPlanOut(BaseModel):
    intent: str
    metric: Optional[str] = None
    filters: dict = {}
    sort: Optional[str] = None
    limit: int = 10
    target_process_id: Optional[int] = None


class AskResponse(BaseModel):
    question: str
    intent: str
    query_plan: QueryPlanOut
    results: Any
    prose_explanation: Optional[str] = None
    unmappable: bool = False
    unmappable_message: Optional[str] = None


# ── LLM Extraction Contract ───────────────────────────────────────────────────

class FactorExtraction(BaseModel):
    ordinal_value: int = Field(..., ge=1, le=5)
    rationale: str = Field(..., min_length=5)
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("ordinal_value")
    @classmethod
    def check_ordinal(cls, v: int) -> int:
        if v not in (1, 2, 3, 4, 5):
            raise ValueError(f"ordinal_value must be 1–5, got {v}")
        return v


class ExtractionResult(BaseModel):
    data_availability: FactorExtraction
    process_repeatability: FactorExtraction
    rule_clarity: FactorExtraction
    volume_frequency: FactorExtraction
    digital_maturity: FactorExtraction
    error_cost_tolerance: FactorExtraction
    human_judgment_dependency: FactorExtraction
    regulatory_safety_constraint: FactorExtraction
    claims: List[str] = Field(default_factory=list, max_length=6)

    def to_factor_dict(self) -> dict[str, FactorExtraction]:
        return {
            "data_availability": self.data_availability,
            "process_repeatability": self.process_repeatability,
            "rule_clarity": self.rule_clarity,
            "volume_frequency": self.volume_frequency,
            "digital_maturity": self.digital_maturity,
            "error_cost_tolerance": self.error_cost_tolerance,
            "human_judgment_dependency": self.human_judgment_dependency,
            "regulatory_safety_constraint": self.regulatory_safety_constraint,
        }


# ── Compare ───────────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    process_ids: List[int] = Field(..., min_length=2, max_length=2)


class FactorComparison(BaseModel):
    factor_key: str
    direction: str
    weight: float
    values: dict   # process_id -> ordinal
    contributions: dict   # process_id -> contribution


class CompareResponse(BaseModel):
    processes: List[ProcessSummary]
    factor_comparisons: List[FactorComparison]
    score_delta: float
