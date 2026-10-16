"""Pydantic schemas for Sprint 7: Governed Procurement Agent, State Machine, Policy Engine, and Human Approval."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.copilot import Citation
from app.schemas.scenario import MitigationScenario


class CaseState(str, Enum):
    """11-step governed state machine states per Blueprint Section 17 & Table 42."""
    DETECTED = "DETECTED"
    HYPOTHESES_ACTIVATED = "HYPOTHESES_ACTIVATED"
    INVESTIGATING = "INVESTIGATING"
    CRITIC_EVALUATING = "CRITIC_EVALUATING"
    ESCALATED_TO_HUMAN = "ESCALATED_TO_HUMAN"
    IMPACT_QUANTIFIED = "IMPACT_QUANTIFIED"
    SCENARIOS_SIMULATED = "SCENARIOS_SIMULATED"
    RECOMMENDATION_GROUNDED = "RECOMMENDATION_GROUNDED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"
    ACTION_PACKET_PREPARED = "ACTION_PACKET_PREPARED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"


class HumanApprovalAction(str, Enum):
    """The four explicit human approval options defined in Table 43."""
    APPROVE = "APPROVE"
    MODIFY = "MODIFY"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    REJECT = "REJECT"


class AuditEvent(BaseModel):
    """Append-only audit record tracking every governance state change."""
    timestamp_utc: str
    from_state: str
    to_state: str
    actor: str
    detail: str
    trace_id: Optional[str] = None


class ProposalActionPacket(BaseModel):
    """Structured, proposal-only mitigation packet with strict read-only ERP boundaries."""
    packet_id: str
    case_id: str
    scenario_id: str
    is_proposal_only: bool = Field(True, description="Strict safety guarantee: no direct ERP/PO write-back")
    target_erp_system: str = "SAP S/4HANA (Simulated Staging Gateway)"
    planned_actions: List[Dict[str, Any]] = Field(default_factory=list)
    total_approved_spend_inr: float = 0.0
    authorized_by_role: str
    authorized_by_actor: str
    approved_at_utc: str
    packet_sha256: str


class ObservedOutcome(BaseModel):
    """Post-decision observed KPI result recorded separately from prediction features."""
    outcome_id: str
    case_id: str
    supplier_id: str
    decision_timestamp_utc: str
    observed_at_utc: str
    action_taken: str
    actual_otif: float = Field(..., ge=0.0, le=1.0)
    actual_service_level: float = Field(..., ge=0.0, le=1.0)
    actual_cost_inr: float = Field(..., ge=0.0)
    outcome_label: str  # "MITIGATED_SUCCESS", "PARTIAL_RECOVERY", "UNRESOLVED_SHORTAGE"
    notes: Optional[str] = None


class HumanApprovalDecision(BaseModel):
    """Human decision payload submitted at the approval workbench."""
    action: HumanApprovalAction
    actor_id: str = Field(..., min_length=2, description="Authenticated user ID")
    actor_role: str = Field(..., description="User role ('SUPPLY_CHAIN_PLANNER', 'PROCUREMENT_MANAGER', 'CPO', 'CATEGORY_DIRECTOR')")
    reason: str = Field(..., min_length=5, description="Mandatory decision rationale or rejection justification")
    idempotency_key: str = Field(..., min_length=8, description="Unique client key preventing duplicate dispatch")
    selected_scenario_id: Optional[str] = "SCN-D"
    modified_allocations: Optional[Dict[str, Any]] = None


class DisruptionCase(BaseModel):
    """Comprehensive governed incident case record tracking full decision loop lifecycle."""
    case_id: str
    trace_id: Optional[str] = None
    supplier_id: str
    supplier_name: str
    state: CaseState
    severity: str = "HIGH"
    created_at_utc: str
    updated_at_utc: str

    # Investigation & Critic
    activated_hypotheses: List[str] = Field(default_factory=list)
    critic_score: float = 0.0
    critic_retries_used: int = 0
    critic_gap_identified: Optional[str] = None

    # Quantitative analysis
    risk_score: float = 0.0
    impact_summary: Optional[Dict[str, Any]] = None
    candidate_scenarios: List[MitigationScenario] = Field(default_factory=list)
    recommended_scenario_id: Optional[str] = None

    # Grounded Copilot Brief
    grounded_brief: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)

    # Governance, Policy & Approval
    policy_evaluation: Optional[Dict[str, Any]] = None
    approval_decision: Optional[HumanApprovalDecision] = None
    action_packet: Optional[ProposalActionPacket] = None

    # Outcomes & Audit
    observed_outcome: Optional[ObservedOutcome] = None
    audit_trail: List[AuditEvent] = Field(default_factory=list)


class CaseCreationRequest(BaseModel):
    """Request to initiate a governed investigation case."""
    supplier_id: str = Field("SUP-1047", description="Supplier to investigate")
    trigger_type: str = Field("SIGNAL_INTELLIGENCE", description="Trigger mechanism ('SIGNAL_INTELLIGENCE', 'METRIC_DEGRADATION', 'MANUAL')")
    disruption_lead_time_days: float = Field(14.0, ge=1.0)
    stockout_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    force_critic_failure: bool = Field(False, description="Testing flag to simulate insufficient evidence and verify escalation")
