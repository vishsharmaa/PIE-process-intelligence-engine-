"""Initial migration — all tables.

Revision ID: 001_initial
Revises:
Create Date: 2024-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── process ──────────────────────────────────────────────────────────
    op.create_table(
        "process",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("external_key", sa.String(128), nullable=True, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "extraction_failed", "failed", name="processstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── extraction_run ───────────────────────────────────────────────────
    op.create_table(
        "extraction_run",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── process_feature ──────────────────────────────────────────────────
    op.create_table(
        "process_feature",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rubric_version", sa.String(32), nullable=False),
        sa.Column("feature_key", sa.String(64), nullable=False),
        sa.Column("ordinal_value", sa.Integer(), nullable=False),
        sa.Column("normalized_value", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("extraction_run_id", sa.Integer(), sa.ForeignKey("extraction_run.id"), nullable=True),
    )

    # ── score ────────────────────────────────────────────────────────────
    op.create_table(
        "score",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rubric_version", sa.String(32), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("band", sa.String(32), nullable=False),
        sa.Column("recommendation", sa.String(64), nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("inputs_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("process_id", "rubric_version", name="uq_score_process_version"),
    )

    # ── score_factor ─────────────────────────────────────────────────────
    op.create_table(
        "score_factor",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("score_id", sa.Integer(), sa.ForeignKey("score.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("factor_key", sa.String(64), nullable=False),
        sa.Column("feature_value", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("contribution", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
    )

    # ── claim ────────────────────────────────────────────────────────────
    op.create_table(
        "claim",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(64), nullable=True),
        sa.Column("supported", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── source ───────────────────────────────────────────────────────────
    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("publisher", sa.String(256), nullable=True),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("doc_type", sa.String(64), nullable=True),
        sa.Column("credibility_tier", sa.Integer(), nullable=True),
    )

    # ── source_chunk ─────────────────────────────────────────────────────
    op.create_table(
        "source_chunk",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("source.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float(), dimensions=1), nullable=True),
    )
    # pgvector column — add via raw SQL for proper vector(768) type
    op.execute("ALTER TABLE source_chunk DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE source_chunk ADD COLUMN embedding vector(768)")

    # ── evidence ─────────────────────────────────────────────────────────
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claim.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_chunk_id", sa.Integer(), sa.ForeignKey("source_chunk.id"), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verification_method", sa.String(64), nullable=True),
    )

    # ── process_rank ─────────────────────────────────────────────────────
    op.create_table(
        "process_rank",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("process.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rubric_version", sa.String(32), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("percentile", sa.Float(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── job ───────────────────────────────────────────────────────────────
    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(64), nullable=False, server_default="ingest"),
        sa.Column("target_process_id", sa.Integer(), sa.ForeignKey("process.id"), nullable=True),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "completed", "failed", name="jobstatus"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("stage", sa.String(64), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )

    # ── rubric_version ───────────────────────────────────────────────────
    op.create_table(
        "rubric_version",
        sa.Column("version", sa.String(32), primary_key=True),
        sa.Column("definition_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── query_log ────────────────────────────────────────────────────────
    op.create_table(
        "query_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(64), nullable=True),
        sa.Column("query_plan_json", sa.JSON(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("query_log")
    op.drop_table("rubric_version")
    op.drop_table("job")
    op.drop_table("process_rank")
    op.drop_table("evidence")
    op.drop_table("source_chunk")
    op.drop_table("source")
    op.drop_table("claim")
    op.drop_table("score_factor")
    op.drop_table("score")
    op.drop_table("process_feature")
    op.drop_table("extraction_run")
    op.drop_table("process")
    op.execute("DROP TYPE IF EXISTS processstatus")
    op.execute("DROP TYPE IF EXISTS jobstatus")
