"""Case management service orchestrating governed cases, approvals, and outcomes."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from app.schemas.cases import (
    AuditEvent,
    CaseCreationRequest,
    CaseState,
    DisruptionCase,
    HumanApprovalAction,
    HumanApprovalDecision,
    ObservedOutcome,
    ProposalActionPacket,
)
from app.core.logging_config import current_trace_id, generate_trace_id
from app.services.agent_orchestrator.state_machine import run_governed_decision_loop
from app.services.policy_engine import check_governance_authorization
from app.db.session import persist_case_record


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class CaseManagementService:
    """Thread-safe in-memory store and orchestrator for governed disruption cases."""

    def __init__(self, data_dir: Path | str = "data/generated"):
        self.data_dir = Path(data_dir)
        self._lock = Lock()
        self._cases: Dict[str, DisruptionCase] = {}
        self._idempotency_registry: Dict[str, str] = {}  # idempotency_key -> case_id

    def create_and_run_case(self, request: CaseCreationRequest) -> DisruptionCase:
        """Initiates and executes a governed decision loop for a supplier."""
        with self._lock:
            case_index = len(self._cases) + 1
            case_id = f"CAS-{request.supplier_id}-{case_index:02d}"

        case = run_governed_decision_loop(
            case_id=case_id,
            supplier_id=request.supplier_id,
            data_dir=self.data_dir,
            disruption_lead_time_days=request.disruption_lead_time_days,
            stockout_probability=request.stockout_probability,
            force_critic_failure=request.force_critic_failure,
        )

        with self._lock:
            self._cases[case.case_id] = case

        persist_case_record(
            case_id=case.case_id,
            supplier_id=case.supplier_id,
            status=case.state.value,
            metadata={"critic_score": case.critic_score, "policy": case.policy_evaluation},
        )

        return case

    def _seed_flagship_case(self) -> DisruptionCase:
        """Seed canonical baseline case for SUP-1047 / DISR-2026-1047 on fresh startup."""
        case = run_governed_decision_loop(
            case_id="CAS-SUP-1047-01",
            supplier_id="SUP-1047",
            data_dir=self.data_dir,
            disruption_lead_time_days=14.0,
            stockout_probability=0.85,
            force_critic_failure=False,
        )
        self._cases[case.case_id] = case
        return case

    def get_case(self, case_id: str) -> Optional[DisruptionCase]:
        with self._lock:
            if not self._cases and case_id == "CAS-SUP-1047-01":
                self._seed_flagship_case()
            return self._cases.get(case_id)

    def list_cases(self) -> List[DisruptionCase]:
        with self._lock:
            if not self._cases:
                self._seed_flagship_case()
            return list(self._cases.values())

    def approve_case(self, case_id: str, decision: HumanApprovalDecision) -> DisruptionCase:
        """Processes human approval workbench actions with deterministic policy enforcement."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                raise KeyError(f"Case {case_id} not found.")

            # 1. Idempotency Check
            if decision.idempotency_key in self._idempotency_registry:
                # Duplicate request: return unchanged existing case record
                return case

            # 2. State Check: Must be awaiting decision or escalated
            valid_pending_states = {CaseState.PENDING_HUMAN_APPROVAL, CaseState.ESCALATED_TO_HUMAN}
            if case.state not in valid_pending_states:
                raise ValueError(
                    f"Case {case_id} is in state '{case.state.value}'; "
                    "human approval action cannot be applied to already resolved cases."
                )

            # 3. Action Dispatch
            ts = _now_utc()
            action = decision.action
            active_trace = current_trace_id.get() or case.trace_id or generate_trace_id("TRC")

            if action == HumanApprovalAction.APPROVE:
                # Find scenario spend
                scenario_id = decision.selected_scenario_id or case.recommended_scenario_id or "SCN-D"
                rec_scen = next((s for s in case.candidate_scenarios if s.scenario_id == scenario_id), None)
                spend = rec_scen.total_mitigation_cost_inr if rec_scen else 1_450_000.0

                # Deterministic Policy Authorization
                auth = check_governance_authorization(
                    actor_role=decision.actor_role,
                    exposure_inr=spend,
                    action_type="supplier_shift",
                    threshold_inr=1_000_000.0,
                )
                if not auth["authorized"]:
                    raise PermissionError(auth["reason"])

                # Prepare Proposal-Only Action Packet
                pkt_seed = f"{case_id}:{scenario_id}:{spend}:{decision.actor_id}:{decision.idempotency_key}"
                pkt_hash = hashlib.sha256(pkt_seed.encode("utf-8")).hexdigest()
                packet_id = f"PKT-{case_id}-{pkt_hash[:8].upper()}"

                planned_actions = [
                    {
                        "action_type": "DUAL_SOURCE_ALLOCATION",
                        "target_supplier": "SUP-1012 (ElectroMotion Technologies)",
                        "allocated_percentage": 40.0,
                        "description": "Shift 40% harness production capacity to pre-qualified secondary supplier.",
                    },
                    {
                        "action_type": "EXPEDITE_BUFFER_STOCK",
                        "target_component": "SKU-WIRE-01",
                        "quantity_units": 500,
                        "description": "Authorize air freight expedite for 500 safety stock units to protect Pune plant.",
                    },
                    {
                        "action_type": "ADVANCE_SUPPLIER_NOTICE",
                        "target_supplier": f"{case.supplier_name} ({case.supplier_id})",
                        "contract_clause": "DOC-MSA-APEX-2025 Section 14 (Disruption Notice)",
                        "description": "Issue formal cure notification requesting recovery plan within 48 hours.",
                    },
                ]

                action_packet = ProposalActionPacket(
                    packet_id=packet_id,
                    case_id=case_id,
                    scenario_id=scenario_id,
                    is_proposal_only=True,
                    target_erp_system="SAP S/4HANA (Simulated Staging Gateway)",
                    planned_actions=planned_actions,
                    total_approved_spend_inr=spend,
                    authorized_by_role=decision.actor_role,
                    authorized_by_actor=decision.actor_id,
                    approved_at_utc=ts,
                    packet_sha256=pkt_hash,
                )

                prev_state = case.state.value
                case.state = CaseState.ACTION_PACKET_PREPARED
                case.approval_decision = decision
                case.action_packet = action_packet
                case.updated_at_utc = ts

                case.audit_trail.append(
                    AuditEvent(
                        timestamp_utc=ts,
                        from_state=prev_state,
                        to_state=CaseState.APPROVED.value,
                        actor=f"{decision.actor_id} ({decision.actor_role})",
                        detail=f"Approved scenario {scenario_id} (spend: ₹{spend:,.2f}). Reason: {decision.reason}",
                        trace_id=active_trace,
                    )
                )
                case.audit_trail.append(
                    AuditEvent(
                        timestamp_utc=ts,
                        from_state=CaseState.APPROVED.value,
                        to_state=CaseState.ACTION_PACKET_PREPARED.value,
                        actor="PROPOSAL_GATEWAY",
                        detail=f"Proposal-only action packet {packet_id} prepared (SHA-256: {pkt_hash[:12]}...). Strictly no live PO write-back.",
                        trace_id=active_trace,
                    )
                )

            elif action == HumanApprovalAction.MODIFY:
                # Custom human modified allocations
                scenario_id = decision.selected_scenario_id or "SCN-D-MODIFIED"
                spend = 1_200_000.0  # Modified spend estimate

                auth = check_governance_authorization(
                    actor_role=decision.actor_role,
                    exposure_inr=spend,
                    action_type="supplier_shift",
                    threshold_inr=1_000_000.0,
                )
                if not auth["authorized"]:
                    raise PermissionError(auth["reason"])

                pkt_seed = f"MOD:{case_id}:{scenario_id}:{spend}:{decision.actor_id}"
                pkt_hash = hashlib.sha256(pkt_seed.encode("utf-8")).hexdigest()
                packet_id = f"PKT-{case_id}-{pkt_hash[:8].upper()}"

                action_packet = ProposalActionPacket(
                    packet_id=packet_id,
                    case_id=case_id,
                    scenario_id=scenario_id,
                    is_proposal_only=True,
                    target_erp_system="SAP S/4HANA (Simulated Staging Gateway)",
                    planned_actions=[
                        {
                            "action_type": "MODIFIED_ALLOCATION",
                            "description": f"Human modified terms: {decision.modified_allocations or 'Adjusted split'}",
                        }
                    ],
                    total_approved_spend_inr=spend,
                    authorized_by_role=decision.actor_role,
                    authorized_by_actor=decision.actor_id,
                    approved_at_utc=ts,
                    packet_sha256=pkt_hash,
                )

                prev_state = case.state.value
                case.state = CaseState.ACTION_PACKET_PREPARED
                case.approval_decision = decision
                case.action_packet = action_packet
                case.updated_at_utc = ts

                case.audit_trail.append(
                    AuditEvent(
                        timestamp_utc=ts,
                        from_state=prev_state,
                        to_state=CaseState.MODIFIED.value,
                        actor=f"{decision.actor_id} ({decision.actor_role})",
                        detail=f"Modified scenario terms: {decision.reason}",
                        trace_id=active_trace,
                    )
                )

            elif action == HumanApprovalAction.REQUEST_MORE_EVIDENCE:
                prev_state = case.state.value
                case.state = CaseState.INVESTIGATING
                case.critic_gap_identified = f"Human requested evidence: {decision.reason}"
                case.updated_at_utc = ts
                case.audit_trail.append(
                    AuditEvent(
                        timestamp_utc=ts,
                        from_state=prev_state,
                        to_state=CaseState.INVESTIGATING.value,
                        actor=f"{decision.actor_id} ({decision.actor_role})",
                        detail=f"Requested additional evidence: {decision.reason}",
                        trace_id=active_trace,
                    )
                )

            elif action == HumanApprovalAction.REJECT:
                prev_state = case.state.value
                case.state = CaseState.REJECTED
                case.approval_decision = decision
                case.updated_at_utc = ts
                case.audit_trail.append(
                    AuditEvent(
                        timestamp_utc=ts,
                        from_state=prev_state,
                        to_state=CaseState.REJECTED.value,
                        actor=f"{decision.actor_id} ({decision.actor_role})",
                        detail=f"Action rejected by user: {decision.reason}",
                        trace_id=active_trace,
                    )
                )

            # Record idempotency key
            self._idempotency_registry[decision.idempotency_key] = case_id
            persist_case_record(
                case_id=case.case_id,
                supplier_id=case.supplier_id,
                status=case.state.value,
                metadata={
                    "actor": decision.actor_id,
                    "role": decision.actor_role,
                    "action": decision.action.value,
                    "packet_id": case.action_packet.packet_id if case.action_packet else None,
                },
            )
            return case

    def record_outcome(self, case_id: str, outcome: ObservedOutcome) -> DisruptionCase:
        """Records post-decision observed operational KPIs separately from prediction features."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                raise KeyError(f"Case {case_id} not found.")

            valid_precursor_states = {
                CaseState.ACTION_PACKET_PREPARED,
                CaseState.APPROVED,
                CaseState.MODIFIED,
                CaseState.REJECTED,
            }
            if case.state not in valid_precursor_states:
                raise ValueError(
                    f"Cannot record outcome for case {case_id} in state '{case.state.value}'. "
                    "Case must be in an actioned or rejected state."
                )

            prev_state = case.state.value
            case.observed_outcome = outcome
            case.state = CaseState.OUTCOME_RECORDED
            case.updated_at_utc = _now_utc()
            active_trace = current_trace_id.get() or case.trace_id or generate_trace_id("TRC")

            case.audit_trail.append(
                AuditEvent(
                    timestamp_utc=case.updated_at_utc,
                    from_state=prev_state,
                    to_state=CaseState.OUTCOME_RECORDED.value,
                    actor="OUTCOME_TRACKING_SERVICE",
                    detail=(
                        f"Post-decision KPI recorded: OTIF={outcome.actual_otif:.1%}, "
                        f"ServiceLevel={outcome.actual_service_level:.1%}, "
                        f"ActualCost=₹{outcome.actual_cost_inr:,.2f}. Label: {outcome.outcome_label}."
                    ),
                    trace_id=active_trace,
                )
            )
            persist_case_record(
                case_id=case.case_id,
                supplier_id=case.supplier_id,
                status=case.state.value,
                metadata={
                    "outcome_id": outcome.outcome_id,
                    "actual_otif": outcome.actual_otif,
                    "actual_service_level": outcome.actual_service_level,
                    "actual_cost_inr": outcome.actual_cost_inr,
                    "outcome_label": outcome.outcome_label,
                },
            )
            return case


# Global service instance
case_service = CaseManagementService()
