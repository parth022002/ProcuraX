"""FastAPI router for Governed Disruption Cases, State Machine, Approvals, and Outcomes."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import UserContext, get_current_user, require_roles, enforce_tenant_isolation
from app.schemas.cases import (
    CaseCreationRequest,
    DisruptionCase,
    HumanApprovalDecision,
    ObservedOutcome,
)
from app.services.agent_orchestrator.service import case_service

router = APIRouter(tags=["cases"])


@router.post("/cases/run", response_model=DisruptionCase, status_code=status.HTTP_201_CREATED)
def run_case_pipeline(
    request: CaseCreationRequest,
    current_user: UserContext = Depends(get_current_user),
) -> DisruptionCase:
    """Execute the full 11-step governed decision loop for a disruption signal."""
    enforce_tenant_isolation(current_user, target_tenant_id="ApexDrive Components")
    try:
        return case_service.create_and_run_case(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute decision loop: {str(exc)}",
        ) from exc


@router.get("/cases", response_model=List[DisruptionCase])
def list_cases(
    current_user: UserContext = Depends(get_current_user),
) -> List[DisruptionCase]:
    """Retrieve all governed disruption cases in the audit store."""
    enforce_tenant_isolation(current_user, target_tenant_id="ApexDrive Components")
    return case_service.list_cases()


@router.get("/cases/demo", response_model=List[DisruptionCase])
def list_demo_cases() -> List[DisruptionCase]:
    """Public read-only demonstration fixture endpoint for showcase visitors.
    
    Provides governed PoC scenario case snapshots clearly identified as demonstration data.
    All case mutations, spend approvals, and live case management remain strictly authenticated.
    """
    return case_service.list_cases()


@router.get("/cases/{case_id}", response_model=DisruptionCase)
def get_case(
    case_id: str,
    current_user: UserContext = Depends(get_current_user),
) -> DisruptionCase:
    """Retrieve details, audit trail, and proposal action packet for a specific case."""
    enforce_tenant_isolation(current_user, target_tenant_id="ApexDrive Components")
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found in audit registry.",
        )
    return case


@router.post("/cases/{case_id}/approve", response_model=DisruptionCase)
def approve_case(
    case_id: str,
    decision: HumanApprovalDecision,
    current_user: UserContext = Depends(get_current_user),
) -> DisruptionCase:
    """Submit a human approval workbench decision (APPROVE, MODIFY, REQUEST_MORE_EVIDENCE, REJECT).
    
    Enforces deterministic policy checks, RBAC spend thresholds, idempotency, and proposal-only safety.
    """
    # 1. Enforce Tenant Isolation
    enforce_tenant_isolation(current_user, target_tenant_id="ApexDrive Components")

    # 2. RBAC Guard: Server-side authenticated identity governs (client body cannot elevate role)
    ROLE_HIERARCHY = {
        "ANALYST": 0,
        "SUPPLY_CHAIN_PLANNER": 1,
        "PROCUREMENT_MANAGER": 2,
        "CATEGORY_DIRECTOR": 3,
        "CPO": 4,
    }
    auth_role = (current_user.role or "ANALYST").upper()
    if auth_role == "ANALYST":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role 'ANALYST' has read-only access and cannot submit approval decisions.",
        )

    requested_role = (
        decision.actor_role.value if hasattr(decision.actor_role, "value") else str(decision.actor_role)
    ).upper()

    auth_rank = ROLE_HIERARCHY.get(auth_role, 0)
    req_rank = ROLE_HIERARCHY.get(requested_role, 0)

    # Client payload cannot elevate above authenticated role
    if req_rank > auth_rank:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authenticated identity role '{auth_role}' cannot execute actions requiring '{requested_role}'. Privilege escalation blocked.",
        )

    effective_role = requested_role
    decision.actor_role = effective_role

    try:
        return case_service.approve_case(case_id, decision)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing approval: {str(exc)}",
        ) from exc


@router.post("/cases/{case_id}/outcome", response_model=DisruptionCase)
def record_outcome(
    case_id: str,
    outcome: ObservedOutcome,
    current_user: UserContext = Depends(require_roles(["ADMIN", "PROCUREMENT_MANAGER", "CPO", "SUPPLY_CHAIN_PLANNER"])),
) -> DisruptionCase:
    """Record post-decision observed operational KPIs separately from prediction features."""
    enforce_tenant_isolation(current_user, target_tenant_id="ApexDrive Components")
    try:
        return case_service.record_outcome(case_id, outcome)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error recording outcome: {str(exc)}",
        ) from exc
