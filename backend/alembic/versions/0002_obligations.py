"""Add regulatory obligations tables."""

from alembic import op
import sqlalchemy as sa

revision = "0002_obligations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulatory_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("regulator", sa.String(100)),
        sa.Column("jurisdiction", sa.String(50)),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("category", sa.String(100), server_default="general"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_status", sa.String(50)),
        sa.Column("success_count", sa.Integer(), server_default="0"),
        sa.Column("failure_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "horizon_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("jurisdiction", sa.String(50), nullable=False),
        sa.Column("regulator", sa.String(100), nullable=False),
        sa.Column("instrument_type", sa.String(100)),
        sa.Column("reference", sa.String(200)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("summary", sa.Text()),
        sa.Column("body", sa.Text()),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("regulatory_sources.id")),
        sa.Column("source_name", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="pending_assessment"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("tags", sa.JSON()),
        sa.Column("candidates", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "policy_docs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("owner", sa.String(255)),
        sa.Column("jurisdiction", sa.String(50)),
        sa.Column("status", sa.String(50), server_default="approved"),
        sa.Column("summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "control_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("policy_id", sa.Uuid(), sa.ForeignKey("policy_docs.id")),
        sa.Column("owner", sa.String(255)),
        sa.Column("type", sa.String(50), server_default="detective"),
        sa.Column("status", sa.String(50), server_default="operating"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "obligations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.String(50), nullable=False),
        sa.Column("regulator", sa.String(100)),
        sa.Column("theme", sa.String(200)),
        sa.Column("owner", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="open"),
        sa.Column("source_horizon_id", sa.Uuid(), sa.ForeignKey("horizon_items.id")),
        sa.Column("source_candidate_id", sa.String(100)),
        sa.Column("source_reference", sa.String(200)),
        sa.Column("due_date", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "gap_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("case_number", sa.String(50), unique=True, nullable=False),
        sa.Column("obligation_id", sa.Uuid(), sa.ForeignKey("obligations.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), server_default="open"),
        sa.Column("gap_status", sa.String(50), server_default="gap"),
        sa.Column("owner", sa.String(255)),
        sa.Column("jurisdiction", sa.String(50)),
        sa.Column("remediation_notes", sa.Text()),
        sa.Column("mappings", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("gap_cases")
    op.drop_table("obligations")
    op.drop_table("control_items")
    op.drop_table("policy_docs")
    op.drop_table("horizon_items")
    op.drop_table("regulatory_sources")
