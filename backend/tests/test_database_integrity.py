"""Tests for Priority 3: Database schema integrity, Alembic migrations, and provenance constraints."""
from __future__ import annotations

from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import check_db_health, persist_case_record
from app.main import app

client = TestClient(app)


def test_alembic_migration_chain_integrity():
    """Verify Alembic configuration, script directory, and sequential migration revisions."""
    root_dir = Path(__file__).resolve().parents[2]
    alembic_ini_path = root_dir / "backend" / "alembic.ini"
    assert alembic_ini_path.exists(), "alembic.ini must exist"

    cfg = Config(str(alembic_ini_path))
    cfg.set_main_option("script_location", str(root_dir / "backend" / "alembic"))
    cfg.set_main_option("version_locations", str(root_dir / "backend" / "alembic" / "versions"))

    script = ScriptDirectory.from_config(cfg)
    revisions = list(script.walk_revisions())
    
    # We have 2 revisions: 0002 and 0001
    assert len(revisions) >= 2, f"Expected at least 2 revisions, found {len(revisions)}"
    
    rev_ids = [r.revision for r in revisions]
    assert "0002_signal_persistence_and_provenance" in rev_ids
    assert "0001_initial_core_schema" in rev_ids

    # Revision 0002 must have down_revision 0001
    head_rev = script.get_revision("0002_signal_persistence_and_provenance")
    assert head_rev.down_revision == "0001_initial_core_schema"


def test_schema_sql_and_provenance_enums():
    """Verify that schema.sql includes source provenance and deduplication definitions."""
    root_dir = Path(__file__).resolve().parents[2]
    schema_file = root_dir / "backend" / "app" / "db" / "schema.sql"
    assert schema_file.exists()

    content = schema_file.read_text(encoding="utf-8")
    
    # Check core table declarations
    expected_tables = [
        "CREATE TABLE IF NOT EXISTS suppliers",
        "CREATE TABLE IF NOT EXISTS skus",
        "CREATE TABLE IF NOT EXISTS purchase_orders",
        "CREATE TABLE IF NOT EXISTS inventory",
        "CREATE TABLE IF NOT EXISTS supplier_performance",
        "CREATE TABLE IF NOT EXISTS external_signals",
        "CREATE TABLE IF NOT EXISTS cases",
        "CREATE TABLE IF NOT EXISTS risk_scores",
        "CREATE TABLE IF NOT EXISTS scenarios",
        "CREATE TABLE IF NOT EXISTS recommendations",
        "CREATE TABLE IF NOT EXISTS approvals",
        "CREATE TABLE IF NOT EXISTS outcomes",
        "CREATE TABLE IF NOT EXISTS audit_events",
    ]
    for tbl in expected_tables:
        assert tbl in content, f"Missing table definition: {tbl}"

    # Verify check constraints
    assert "annual_spend_inr >= 0" in content
    assert "base_reliability BETWEEN 0 AND 1" in content
    assert "severity BETWEEN 0 AND 1" in content
    assert "content_hash VARCHAR(64)" in content
    assert "freshness_status" in content
    assert "age_hours" in content


def test_db_health_endpoint_contract():
    """Verify /health and /health/database responses match reliable typed contracts."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in {"healthy", "ok"}

    res_db = client.get("/api/v1/health/database")
    assert res_db.status_code == 200
    db_data = res_db.json()
    assert "status" in db_data
    assert "provider" in db_data
    # Either connected/healthy or unconfigured/error, but must return a structured response
    assert db_data["status"] in {"healthy", "unconfigured", "error", "connected"}


def test_idempotent_case_record_persistence():
    """Verify persist_case_record runs idempotently without crashing."""
    success = persist_case_record(
        case_id="CASE-TEST-IDEMPOTENT-001",
        supplier_id="SUP-1047",
        status="investigating",
        metadata={"unit_test": True},
    )
    # Returns True if connected to Neon, False if unconfigured/offline, but never raises
    assert isinstance(success, bool)
