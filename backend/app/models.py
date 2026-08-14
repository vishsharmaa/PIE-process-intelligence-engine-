import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, UniqueConstraint, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db import Base


class ProcessStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    extraction_failed = "extraction_failed"
    failed = "failed"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Process(Base):
    __tablename__ = "process"

    id = Column(Integer, primary_key=True, index=True)
    external_key = Column(String(128), index=True, nullable=True)
    name = Column(String(256), nullable=False)
    raw_description = Column(Text, nullable=False)
    department = Column(String(128), nullable=True)
    normalized_text = Column(Text, nullable=True)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    industry = Column(String(128), nullable=True)
    status = Column(SAEnum(ProcessStatus), default=ProcessStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    features = relationship("ProcessFeature", back_populates="process", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="process", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="process", cascade="all, delete-orphan")
    ranks = relationship("ProcessRank", back_populates="process", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="process")
    extraction_runs = relationship("ExtractionRun", back_populates="process")


class ProcessFeature(Base):
    __tablename__ = "process_feature"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True)
    rubric_version = Column(String(32), nullable=False)
    feature_key = Column(String(64), nullable=False)
    ordinal_value = Column(Integer, nullable=False)      # 1–5
    normalized_value = Column(Float, nullable=False)     # 0..1
    rationale = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)            # 0..1
    extraction_run_id = Column(Integer, ForeignKey("extraction_run.id"), nullable=True)

    process = relationship("Process", back_populates="features")
    extraction_run = relationship("ExtractionRun")


class Score(Base):
    __tablename__ = "score"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True)
    rubric_version = Column(String(32), nullable=False)
    total_score = Column(Float, nullable=False)
    band = Column(String(32), nullable=False)            # Automate / Augment / Human-Led
    recommendation = Column(String(64), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    inputs_hash = Column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("process_id", "rubric_version", name="uq_score_process_version"),)

    process = relationship("Process", back_populates="scores")
    factors = relationship("ScoreFactor", back_populates="score", cascade="all, delete-orphan")


class ScoreFactor(Base):
    __tablename__ = "score_factor"

    id = Column(Integer, primary_key=True, index=True)
    score_id = Column(Integer, ForeignKey("score.id", ondelete="CASCADE"), nullable=False, index=True)
    factor_key = Column(String(64), nullable=False)
    feature_value = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    contribution = Column(Float, nullable=False)
    direction = Column(String(8), nullable=False)        # '+' or '-'

    score = relationship("Score", back_populates="factors")


class Claim(Base):
    __tablename__ = "claim"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(64), nullable=True)
    supported = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    process = relationship("Process", back_populates="claims")
    evidence_items = relationship("Evidence", back_populates="claim", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claim.id", ondelete="CASCADE"), nullable=False, index=True)
    source_chunk_id = Column(Integer, ForeignKey("source_chunk.id"), nullable=True)
    quote = Column(Text, nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    verification_method = Column(String(64), nullable=True)

    claim = relationship("Claim", back_populates="evidence_items")
    source_chunk = relationship("SourceChunk", back_populates="evidence_items")


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    publisher = Column(String(256), nullable=True)
    url = Column(String(1024), nullable=True)
    year = Column(Integer, nullable=True)
    doc_type = Column(String(64), nullable=True)
    credibility_tier = Column(Integer, nullable=True)   # 1 = highest

    chunks = relationship("SourceChunk", back_populates="source", cascade="all, delete-orphan")


class SourceChunk(Base):
    __tablename__ = "source_chunk"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("source.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)

    source = relationship("Source", back_populates="chunks")
    evidence_items = relationship("Evidence", back_populates="source_chunk")


class ProcessRank(Base):
    __tablename__ = "process_rank"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True)
    rubric_version = Column(String(32), nullable=False)
    rank = Column(Integer, nullable=False)
    percentile = Column(Float, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    process = relationship("Process", back_populates="ranks")


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(64), nullable=False, default="ingest")
    target_process_id = Column(Integer, ForeignKey("process.id"), nullable=True)
    status = Column(SAEnum(JobStatus), default=JobStatus.queued, nullable=False)
    stage = Column(String(64), nullable=True)
    progress = Column(Float, default=0.0, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    process = relationship("Process", back_populates="jobs")


class ExtractionRun(Base):
    __tablename__ = "extraction_run"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True)
    model = Column(String(128), nullable=False)
    prompt_version = Column(String(32), nullable=False)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    process = relationship("Process", back_populates="extraction_runs")


class RubricVersion(Base):
    __tablename__ = "rubric_version"

    version = Column(String(32), primary_key=True)
    definition_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)


class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    intent = Column(String(64), nullable=True)
    query_plan_json = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
