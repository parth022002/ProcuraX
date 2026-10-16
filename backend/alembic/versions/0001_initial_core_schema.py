"""Initial core schema migration for ProcuraX

Revision ID: 0001_initial_core_schema
Revises: 
Create Date: 2026-10-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_core_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Suppliers master table
    op.create_table(
        "suppliers",
        sa.Column("supplier_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("strategic_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("annual_spend_inr", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("base_reliability", sa.Numeric(5, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("supplier_id"),
        sa.CheckConstraint("annual_spend_inr >= 0", name="ck_suppliers_spend_nonneg"),
        sa.CheckConstraint("base_reliability BETWEEN 0 AND 1", name="ck_suppliers_reliability_range"),
    )

    # SKUs table
    op.create_table(
        "skus",
        sa.Column("sku_id", sa.Text(), nullable=False),
        sa.Column("family", sa.Text(), nullable=False),
        sa.Column("unit_contribution_margin_inr", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("criticality", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("sku_id"),
        sa.CheckConstraint("unit_contribution_margin_inr >= 0", name="ck_skus_margin_nonneg"),
        sa.CheckConstraint("criticality BETWEEN 1 AND 5", name="ck_skus_criticality_range"),
    )

    # Purchase orders table
    op.create_table(
        "purchase_orders",
        sa.Column("po_id", sa.Text(), nullable=False),
        sa.Column("supplier_id", sa.Text(), nullable=False),
        sa.Column("sku_id", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("promised_date", sa.Date(), nullable=False),
        sa.Column("actual_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.sku_id"]),
        sa.PrimaryKeyConstraint("po_id"),
        sa.CheckConstraint("quantity > 0", name="ck_po_quantity_pos"),
        sa.CheckConstraint("promised_date >= order_date", name="ck_po_promised_after_order"),
    )
    op.create_index("ix_purchase_orders_supplier_date", "purchase_orders", ["supplier_id", "order_date"])
    op.create_index("ix_purchase_orders_sku_date", "purchase_orders", ["sku_id", "order_date"])

    # Inventory table
    op.create_table(
        "inventory",
        sa.Column("inventory_id", sa.Text(), nullable=False),
        sa.Column("sku_id", sa.Text(), nullable=False),
        sa.Column("plant", sa.Text(), nullable=False),
        sa.Column("on_hand_units", sa.Integer(), nullable=False),
        sa.Column("safety_stock_units", sa.Integer(), nullable=False),
        sa.Column("average_daily_consumption", sa.Numeric(12, 3), nullable=False),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.sku_id"]),
        sa.PrimaryKeyConstraint("inventory_id"),
        sa.UniqueConstraint("sku_id", "plant", name="uq_inventory_sku_plant"),
        sa.CheckConstraint("on_hand_units >= 0", name="ck_inv_on_hand_nonneg"),
        sa.CheckConstraint("safety_stock_units >= 0", name="ck_inv_safety_nonneg"),
        sa.CheckConstraint("average_daily_consumption >= 0", name="ck_inv_consumption_nonneg"),
    )

    # Supplier performance monthly history
    op.create_table(
        "supplier_performance",
        sa.Column("performance_id", sa.Text(), nullable=False),
        sa.Column("supplier_id", sa.Text(), nullable=False),
        sa.Column("period_date", sa.Date(), nullable=False),
        sa.Column("otif", sa.Numeric(5, 4), nullable=True),
        sa.Column("lead_time_days", sa.Numeric(10, 2), nullable=False),
        sa.Column("defect_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("capacity_utilisation", sa.Numeric(5, 4), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.PrimaryKeyConstraint("performance_id"),
        sa.UniqueConstraint("supplier_id", "period_date", name="uq_perf_supplier_period"),
        sa.CheckConstraint("otif BETWEEN 0 AND 1", name="ck_perf_otif_range"),
        sa.CheckConstraint("lead_time_days >= 0", name="ck_perf_lead_time_nonneg"),
        sa.CheckConstraint("defect_rate BETWEEN 0 AND 1", name="ck_perf_defect_range"),
        sa.CheckConstraint("capacity_utilisation BETWEEN 0 AND 1", name="ck_perf_cap_range"),
    )

    # External signals table
    op.create_table(
        "external_signals",
        sa.Column("signal_id", sa.Text(), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("supplier_id", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("material", sa.Text(), nullable=True),
        sa.Column("severity", sa.Numeric(5, 4), nullable=True),
        sa.Column("source_credibility", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.PrimaryKeyConstraint("signal_id"),
        sa.CheckConstraint("severity BETWEEN 0 AND 1", name="ck_signals_severity_range"),
        sa.CheckConstraint("source_credibility BETWEEN 0 AND 1", name="ck_signals_credibility_range"),
    )

    # Cases table
    op.create_table(
        "cases",
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("supplier_id", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.Text(), server_default="investigating", nullable=False),
        sa.Column("prediction_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.PrimaryKeyConstraint("case_id"),
    )

    # Risk scores table
    op.create_table(
        "risk_scores",
        sa.Column("risk_id", sa.Text(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=True),
        sa.Column("supplier_id", sa.Text(), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prediction_probability", sa.Numeric(7, 6), nullable=True),
        sa.Column("governed_score", sa.SmallInteger(), nullable=True),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("driver_values", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("score_config_version", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.PrimaryKeyConstraint("risk_id"),
        sa.CheckConstraint("prediction_probability BETWEEN 0 AND 1", name="ck_risk_prob_range"),
        sa.CheckConstraint("governed_score BETWEEN 0 AND 100", name="ck_risk_gov_score_range"),
    )

    # Scenarios table
    op.create_table(
        "scenarios",
        sa.Column("scenario_id", sa.Text(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("scenario_type", sa.Text(), nullable=False),
        sa.Column("feasible", sa.Boolean(), nullable=False),
        sa.Column("infeasibility_reason", sa.Text(), nullable=True),
        sa.Column("objective_value_inr", sa.Numeric(18, 2), nullable=True),
        sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("solver_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.PrimaryKeyConstraint("scenario_id"),
    )

    # Recommendations table
    op.create_table(
        "recommendations",
        sa.Column("recommendation_id", sa.Text(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("scenario_id", sa.Text(), nullable=True),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("abstained", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.scenario_id"]),
        sa.PrimaryKeyConstraint("recommendation_id"),
    )

    # Approvals table
    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.Text(), nullable=False),
        sa.Column("recommendation_id", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("actor_role", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("policy_result", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.recommendation_id"]),
        sa.PrimaryKeyConstraint("approval_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_approvals_idempotency_key"),
        sa.CheckConstraint("decision IN ('approve','modify','request_evidence','reject','escalate')", name="ck_approvals_decision"),
    )

    # Outcomes table
    op.create_table(
        "outcomes",
        sa.Column("outcome_id", sa.Text(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("decision_id", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_otif", sa.Numeric(5, 4), nullable=True),
        sa.Column("actual_service_level", sa.Numeric(5, 4), nullable=True),
        sa.Column("actual_cost_inr", sa.Numeric(18, 2), nullable=True),
        sa.Column("business_result", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("outcome_label", sa.Text(), nullable=True),
        sa.Column("dataset_partition", sa.Text(), server_default="post_decision", nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.PrimaryKeyConstraint("outcome_id"),
    )

    # Audit events table (Append-only)
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.PrimaryKeyConstraint("event_id"),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("outcomes")
    op.drop_table("approvals")
    op.drop_table("recommendations")
    op.drop_table("scenarios")
    op.drop_table("risk_scores")
    op.drop_table("cases")
    op.drop_table("external_signals")
    op.drop_table("supplier_performance")
    op.drop_table("inventory")
    op.drop_table("purchase_orders")
    op.drop_table("skus")
    op.drop_table("suppliers")
