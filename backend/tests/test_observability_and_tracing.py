"""Acceptance Tests for Milestone 6: Observability, Distributed Tracing & Operational Error Governance."""
from __future__ import annotations

import json
import logging
from fastapi.testclient import TestClient

from app.main import app
from app.core.logging_config import StructuredJsonFormatter, generate_trace_id

client = TestClient(app)


# ==============================================================================
# 1. Distributed Tracing & Response Correlation Headers
# ==============================================================================

def test_every_response_injects_trace_headers():
    """Verify that every HTTP response includes X-Trace-ID and X-Request-ID headers."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-trace-id" in response.headers
    assert response.headers["x-trace-id"].startswith("TRC-")
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"].startswith("REQ-")


def test_custom_trace_id_is_preserved_and_echoed():
    """Verify that a client-provided X-Trace-ID is propagated through execution."""
    custom_trace = "TRC-CLIENT-ENTERPRISE-999"
    response = client.get("/api/v1/health", headers={"X-Trace-ID": custom_trace})
    assert response.status_code == 200
    assert response.headers.get("x-trace-id") == custom_trace


# ==============================================================================
# 2. Trace Propagation into State Machine & Append-Only Audit Trail
# ==============================================================================

def test_governed_case_and_all_audit_events_capture_trace_id():
    """Verify that DisruptionCase and each AuditEvent record persistent trace_id correlation."""
    custom_trace = "TRC-CASE-AUDIT-TRACE-101"
    response = client.post(
        "/api/v1/cases/run",
        json={"supplier_id": "SUP-1047"},
        headers={"X-Trace-ID": custom_trace},
    )
    assert response.status_code == 201
    case = response.json()
    assert case["trace_id"] == custom_trace

    # Verify every audit event captures trace_id
    assert len(case["audit_trail"]) >= 8
    for event in case["audit_trail"]:
        assert event["trace_id"] == custom_trace, f"Audit event {event['to_state']} missing trace_id"


def test_case_approval_audit_events_preserve_trace_id():
    """Verify that human approval actions attach trace_id to action packet audit records."""
    # 1. Run case
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    # 2. Approve case with custom trace
    custom_trace = "TRC-CPO-SIGN-OFF-002"
    approve_resp = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "APPROVE",
            "actor_id": "USR-CPO-01",
            "actor_role": "CPO",
            "reason": "Authorized dual-sourcing mitigation spend",
            "idempotency_key": "IDEM-OBSERVABILITY-001",
            "selected_scenario_id": "SCN-D",
        },
        headers={"X-Trace-ID": custom_trace, "X-User-Role": "CPO"},
    )
    assert approve_resp.status_code == 200
    case = approve_resp.json()
    
    # Check that new audit records recorded the trace
    recent_events = case["audit_trail"][-2:]
    for ev in recent_events:
        assert ev["trace_id"] == custom_trace


def test_outcome_recording_audit_event_captures_trace_id():
    """Verify that post-decision outcome records capture trace_id."""
    # 1. Run and approve case
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]
    client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "APPROVE",
            "actor_id": "USR-CPO-01",
            "actor_role": "CPO",
            "reason": "Approved for outcome testing",
            "idempotency_key": "IDEM-OUTCOME-TEST-002",
            "selected_scenario_id": "SCN-D",
        },
        headers={"X-User-Role": "CPO"},
    )

    # 2. Record outcome
    custom_trace = "TRC-OUTCOME-AUDIT-003"
    outcome_resp = client.post(
        f"/api/v1/cases/{case_id}/outcome",
        json={
            "outcome_id": f"OUT-{case_id}",
            "case_id": case_id,
            "supplier_id": "SUP-1047",
            "decision_timestamp_utc": "2026-10-16T10:00:00Z",
            "observed_at_utc": "2026-10-16T12:00:00Z",
            "action_taken": "DUAL_SOURCE_ALLOCATION",
            "actual_otif": 0.94,
            "actual_service_level": 0.97,
            "actual_cost_inr": 1380000.0,
            "outcome_label": "MITIGATED_SUCCESS",
        },
        headers={"X-Trace-ID": custom_trace},
    )
    assert outcome_resp.status_code == 200
    case = outcome_resp.json()
    latest_event = case["audit_trail"][-1]
    assert latest_event["to_state"] == "OUTCOME_RECORDED"
    assert latest_event["trace_id"] == custom_trace


# ==============================================================================
# 3. Standardized Operational Error Envelope
# ==============================================================================

def test_operational_error_contains_structured_envelope_and_next_action():
    """Verify that HTTP errors return structured envelopes with next_permitted_action."""
    custom_trace = "TRC-ERR-ENVELOPE-004"
    response = client.get(
        "/api/v1/suppliers/SUP-UNKNOWN-9999/360",
        headers={"X-Trace-ID": custom_trace},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "HTTP_404"
    assert "not found" in data["detail"].lower()
    assert data["trace_id"] == custom_trace
    assert "next_permitted_action" in data
    assert "authoritative inventory and supplier registry" in data["next_permitted_action"]


def test_tenant_mismatch_error_provides_actionable_next_step():
    """Verify that tenant mismatch errors guide user on next permitted action."""
    response = client.get(
        "/api/v1/cases",
        headers={"X-Tenant-ID": "CompetitorMotors Global"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "HTTP_403"
    assert "ApexDrive Components" in data["next_permitted_action"]


# ==============================================================================
# 4. Provider Telemetry & Health Monitoring
# ==============================================================================

def test_provider_health_telemetry_fields():
    """Verify that provider health monitoring returns latency, circuit breaker, and freshness windows."""
    response = client.get("/api/v1/signals/providers")
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) >= 5
    for p in providers:
        assert "provider" in p
        assert "configured" in p
        assert "status" in p
        assert "latency_ms" in p
        assert p["circuit_breaker_status"] in {"CLOSED", "OPEN", "HALF_OPEN"}
        assert p["freshness_window_hours"] == 24


# ==============================================================================
# 5. Structured JSON Log Formatter
# ==============================================================================

def test_structured_json_formatter_outputs_valid_json():
    """Verify that the StructuredJsonFormatter produces valid JSON with required fields."""
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Sample governance audit log event",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Sample governance audit log event"
    assert "timestamp_iso" in parsed
