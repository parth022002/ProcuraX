"""Minimal deterministic approval policy. This is not yet wired to an API or persistence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionContext:
    action_type: str
    exposure_inr: float
    actor_role: str
    approval_threshold_inr: float
    human_approved: bool = False


ALLOWED_ACTIONS = {"purchase_request", "supplier_shift", "inventory_transfer", "expedite", "internal_notification", "report_draft"}
MATERIAL_ACTIONS = {"purchase_request", "supplier_shift", "inventory_transfer", "expedite"}


def evaluate_action(context: ActionContext) -> dict[str, str | bool]:
    if context.exposure_inr < 0 or context.approval_threshold_inr < 0:
        raise ValueError("Exposure and threshold must be non-negative")
    if context.action_type not in ALLOWED_ACTIONS:
        return {"authorised": False, "reason": "action_not_allowed", "requires_human_approval": False}
    requires_human = (
        context.action_type in MATERIAL_ACTIONS
        and context.exposure_inr >= context.approval_threshold_inr
    )
    allowed_roles = {"procurement_manager", "cpo", "category_director", "admin"}
    actor_norm = context.actor_role.lower().strip()
    role_allowed = actor_norm in allowed_roles
    if not role_allowed:
        return {"authorised": False, "reason": "role_not_allowed", "requires_human_approval": requires_human}
    if requires_human and not context.human_approved:
        return {"authorised": False, "reason": "human_approval_required", "requires_human_approval": True}
    return {"authorised": True, "reason": "policy_passed", "requires_human_approval": requires_human}


def check_governance_authorization(
    actor_role: str,
    exposure_inr: float,
    action_type: str = "supplier_shift",
    threshold_inr: float = 1_000_000.0,
) -> dict[str, Any]:
    """Evaluates whether an actor role is authorized to approve spend under Blueprint Section 17/18.
    
    Rules:
    - Material spend <= ₹10,00,000 can be approved by SUPPLY_CHAIN_PLANNER or PROCUREMENT_MANAGER.
    - Material spend > ₹10,00,000 strictly requires CPO, CATEGORY_DIRECTOR, or ADMIN.
    """
    role_norm = actor_role.lower().strip()
    if role_norm not in {"procurement_manager", "cpo", "category_director", "admin", "supply_chain_planner"}:
        return {
            "authorized": False,
            "required_role": "PROCUREMENT_MANAGER or CPO",
            "reason": f"Role '{actor_role}' has no procurement approval authority.",
        }

    high_exposure = exposure_inr > threshold_inr
    if high_exposure and role_norm not in {"cpo", "category_director", "admin"}:
        return {
            "authorized": False,
            "required_role": "CPO or CATEGORY_DIRECTOR",
            "reason": (
                f"Action spend ₹{exposure_inr:,.2f} exceeds ₹{threshold_inr:,.2f} threshold. "
                f"Role '{actor_role}' is not authorized; CPO or Category Director approval is mandatory."
            ),
        }

    return {
        "authorized": True,
        "required_role": "CPO" if high_exposure else "PROCUREMENT_MANAGER",
        "reason": f"Policy approved: Role '{actor_role}' has sufficient governance authority.",
    }

