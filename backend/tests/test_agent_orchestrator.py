"""Acceptance tests for Sprint 7: Governed Procurement Agent, State Machine, Policy Engine & Human Approval."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.cases import CaseState

client = TestClient(app)


def test_full_governed_decision_loop_reaches_approval_gate():
    """Verify end-to-end 11-step progression for SUP-1047 up to PENDING_HUMAN_APPROVAL."""
    response = client.post(
        "/api/v1/cases/run",
        json={
            "supplier_id": "SUP-1047",
            "trigger_type": "SIGNAL_INTELLIGENCE",
            "disruption_lead_time_days": 14.0,
            "force_critic_failure": False,
        },
    )
    assert response.status_code == 201
    case = response.json()

    assert case["case_id"].startswith("CAS-SUP-1047-")
    assert case["state"] == CaseState.PENDING_HUMAN_APPROVAL.value
    assert case["supplier_name"] == "ApexDrive Components"
    assert len(case["activated_hypotheses"]) >= 3

    # Verify Critic passed
    assert case["critic_score"] >= 0.60
    assert case["critic_retries_used"] == 0

    # Verify Impact Quantified
    assert case["impact_summary"] is not None
    assert case["impact_summary"]["total_revenue_exposure_inr"] > 0
    assert case["impact_summary"]["affected_sku_count"] > 0
    assert len(case["impact_summary"]["sku_impacts"]) > 0

    # Verify Scenarios Simulated
    assert len(case["candidate_scenarios"]) == 4
    assert case["recommended_scenario_id"] in {"SCN-D", "SCN-B", "SCN-C"}

    # Verify Grounded Copilot Brief
    assert len(case["citations"]) > 0
    assert "DOC-" in case["citations"][0]["document_id"]

    # Verify Policy Evaluation requires CPO due to spend > ₹10L
    assert case["policy_evaluation"]["spend_threshold_inr"] == 1_000_000.0
    assert "CPO" in case["policy_evaluation"]["required_role"]

    # Verify Audit Trail captures complete lineage
    audit_states = [e["to_state"] for e in case["audit_trail"]]
    assert "DETECTED" in audit_states
    assert "HYPOTHESES_ACTIVATED" in audit_states
    assert "INVESTIGATING" in audit_states
    assert "IMPACT_QUANTIFIED" in audit_states
    assert "SCENARIOS_SIMULATED" in audit_states
    assert "RECOMMENDATION_GROUNDED" in audit_states
    assert "POLICY_EVALUATED" in audit_states
    assert "PENDING_HUMAN_APPROVAL" in audit_states


def test_critic_gate_enforces_one_retry_and_escalates_to_human():
    """Verify that insufficient evidence retries exactly once then halts at ESCALATED_TO_HUMAN."""
    response = client.post(
        "/api/v1/cases/run",
        json={
            "supplier_id": "SUP-1047",
            "trigger_type": "SIGNAL_INTELLIGENCE",
            "disruption_lead_time_days": 14.0,
            "force_critic_failure": True,
        },
    )
    assert response.status_code == 201
    case = response.json()

    assert case["state"] == CaseState.ESCALATED_TO_HUMAN.value
    assert case["critic_retries_used"] == 1
    assert case["critic_gap_identified"] is not None
    # Crucial guarantee: state did NOT advance to impact quantification or scenario simulation
    assert case["impact_summary"] is None
    assert len(case["candidate_scenarios"]) == 0

    audit_states = [e["to_state"] for e in case["audit_trail"]]
    assert "ESCALATED_TO_HUMAN" in audit_states


def test_policy_engine_denies_low_role_for_material_spend():
    """Verify that SUPPLY_CHAIN_PLANNER is blocked from approving spend above ₹10,00,000."""
    # 1. Run case to reach PENDING_HUMAN_APPROVAL
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    # 2. Supply chain planner attempts approval on > ₹10L spend
    approve_resp = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "APPROVE",
            "actor_id": "USR-PLANNER-01",
            "actor_role": "SUPPLY_CHAIN_PLANNER",
            "reason": "Routine shift to secondary supplier",
            "idempotency_key": "IDEM-TEST-PLANNER-DENIED-001",
            "selected_scenario_id": "SCN-D",
        },
    )
    assert approve_resp.status_code == 403
    assert "CPO or Category Director approval is mandatory" in approve_resp.json()["detail"]


def test_authorized_cpo_approval_creates_proposal_only_action_packet():
    """Verify that CPO can authorize high-spend mitigation, creating a proposal-only packet."""
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    approve_resp = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "APPROVE",
            "actor_id": "USR-CPO-01",
            "actor_role": "CPO",
            "reason": "Authorized per Dual Sourcing Policy emergency clause 4.2",
            "idempotency_key": "IDEM-TEST-CPO-APPROVED-001",
            "selected_scenario_id": "SCN-D",
        },
    )
    assert approve_resp.status_code == 200
    case = approve_resp.json()

    assert case["state"] == CaseState.ACTION_PACKET_PREPARED.value
    packet = case["action_packet"]
    assert packet is not None
    assert packet["is_proposal_only"] is True  # Strict safety guarantee!
    assert packet["total_approved_spend_inr"] > 1_000_000.0
    assert packet["authorized_by_role"] == "CPO"
    assert len(packet["packet_sha256"]) == 64
    assert len(packet["planned_actions"]) >= 3


def test_idempotent_approval_submission():
    """Submitting the exact same approval with identical idempotency key returns cached record without error."""
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    payload = {
        "action": "APPROVE",
        "actor_id": "USR-CPO-01",
        "actor_role": "CPO",
        "reason": "Authorized emergency dual-source ramp",
        "idempotency_key": "IDEM-KEY-IDENTICAL-099",
        "selected_scenario_id": "SCN-D",
    }
    resp1 = client.post(f"/api/v1/cases/{case_id}/approve", json=payload)
    assert resp1.status_code == 200
    audit_len_1 = len(resp1.json()["audit_trail"])

    # Duplicate submission
    resp2 = client.post(f"/api/v1/cases/{case_id}/approve", json=payload)
    assert resp2.status_code == 200
    assert len(resp2.json()["audit_trail"]) == audit_len_1


def test_human_modify_action_generates_action_packet():
    """Verify human modification updates allocations and produces valid proposal packet."""
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    mod_resp = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "MODIFY",
            "actor_id": "USR-CPO-01",
            "actor_role": "CPO",
            "reason": "Shift 30% volume instead of 40% to manage cash flow",
            "idempotency_key": "IDEM-KEY-MODIFY-001",
            "selected_scenario_id": "SCN-D",
            "modified_allocations": {"electro_motion_share": 0.30, "apex_share": 0.70},
        },
    )
    assert mod_resp.status_code == 200
    case = mod_resp.json()
    assert case["state"] == CaseState.ACTION_PACKET_PREPARED.value
    assert case["action_packet"]["is_proposal_only"] is True


def test_human_rejection_halts_mitigation():
    """Verify that human rejection transitions case to REJECTED."""
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    rej_resp = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "REJECT",
            "actor_id": "USR-DIRECTOR-01",
            "actor_role": "CATEGORY_DIRECTOR",
            "reason": "Disruption deemed transitory; buffer stock sufficient for next 10 days.",
            "idempotency_key": "IDEM-KEY-REJECT-001",
        },
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["state"] == CaseState.REJECTED.value


def test_post_decision_observed_outcome_recording():
    """Verify recording post-decision observed operational KPIs separately from prediction features."""
    # 1. Run and approve case
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "APPROVE",
            "actor_id": "USR-CPO-01",
            "actor_role": "CPO",
            "reason": "Approved dual source",
            "idempotency_key": "IDEM-KEY-OUTCOME-SETUP-01",
            "selected_scenario_id": "SCN-D",
        },
    )

    # 2. Record post-decision observed outcome
    outcome_resp = client.post(
        f"/api/v1/cases/{case_id}/outcome",
        json={
            "outcome_id": f"OUT-{case_id}-01",
            "case_id": case_id,
            "supplier_id": "SUP-1047",
            "decision_timestamp_utc": "2026-10-14T10:00:00Z",
            "observed_at_utc": "2026-10-28T10:00:00Z",
            "action_taken": "HYBRID_DUAL_SOURCE_AND_EXPEDITE",
            "actual_otif": 0.94,
            "actual_service_level": 0.98,
            "actual_cost_inr": 1_420_000.0,
            "outcome_label": "MITIGATED_SUCCESS",
            "notes": "Assembly plants in Pune and Chennai maintained full uptime without downtime.",
        },
    )
    assert outcome_resp.status_code == 200
    case = outcome_resp.json()
    assert case["state"] == CaseState.OUTCOME_RECORDED.value
    assert case["observed_outcome"]["actual_otif"] == 0.94
    assert case["observed_outcome"]["outcome_label"] == "MITIGATED_SUCCESS"
