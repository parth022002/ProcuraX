"""Add signal persistence columns, deduplication indices, and provenance constraints

Revision ID: 0002_signal_persistence_and_provenance
Revises: 0001_initial_core_schema
Create Date: 2026-10-16 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_signal_persistence_and_provenance"
down_revision: Union[str, None] = "0001_initial_core_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add persistence and deduplication columns to external_signals
    op.add_column("external_signals", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("external_signals", sa.Column("canonical_url", sa.Text(), nullable=True))
    op.add_column("external_signals", sa.Column("freshness_status", sa.String(length=32), server_default="fresh", nullable=False))
    op.add_column("external_signals", sa.Column("age_hours", sa.Numeric(8, 2), nullable=True))
    op.add_column("external_signals", sa.Column("persisted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    
    # Create index for fast hash lookups and deduplication
    op.create_index("ix_external_signals_content_hash", "external_signals", ["content_hash"])
    op.create_index("ix_external_signals_supplier_id", "external_signals", ["supplier_id"])
    op.create_index("ix_external_signals_event_type", "external_signals", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_external_signals_event_type", table_name="external_signals")
    op.drop_index("ix_external_signals_supplier_id", table_name="external_signals")
    op.drop_index("ix_external_signals_content_hash", table_name="external_signals")
    op.drop_column("external_signals", "persisted_at")
    op.drop_column("external_signals", "age_hours")
    op.drop_column("external_signals", "freshness_status")
    op.drop_column("external_signals", "canonical_url")
    op.drop_column("external_signals", "content_hash")
