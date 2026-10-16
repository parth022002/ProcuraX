"""Structured, schema-validated contract and policy constraint extraction.
Precedes optimization solver to ensure constraints originate from authoritative records,
never from ungrounded LLM numeric generation.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from app.schemas.scenario import ContractConstraints

# Authoritative contract repository for flagship suppliers
CONTRACT_REGISTRY: Dict[str, Dict] = {
    "SUP-1047": {
        "contract_id": "CNT-APEX-2025-08",
        "supplier_id": "SUP-1047",
        "supplier_name": "ApexDrive Components Pvt. Ltd.",
        "is_approved_vendor": True,
        "alternate_sourcing_permitted": True,
        "moq_units": 500.0,
        "capacity_ceiling_units": 45_000.0,
        "standard_lead_time_days": 14.0,
        "expedite_lead_time_days": 4.0,
        "expedite_premium_rate": 0.35,  # 35% surcharge for express air freight / dedicated transport
        "unit_purchase_price_inr": 2_850.0,
        "penalty_rate_per_day_inr": 25_000.0,
        "switching_or_tooling_cost_inr": 0.0,
        "requires_manual_review": False,
        "source_clause_ref": "ApexDrive MSA Section 4.2 (Order Multiples) & Schedule B (Expedite Terms)",
    },
    "SUP-1012": {
        "contract_id": "CNT-ELECTRO-2025-03",
        "supplier_id": "SUP-1012",
        "supplier_name": "ElectroMotion Systems India Pvt. Ltd.",
        "is_approved_vendor": True,
        "alternate_sourcing_permitted": True,
        "moq_units": 1_000.0,
        "capacity_ceiling_units": 50_000.0,
        "standard_lead_time_days": 10.0,
        "expedite_lead_time_days": 3.0,
        "expedite_premium_rate": 0.25,
        "unit_purchase_price_inr": 2_950.0,  # +₹100/unit price delta compared to primary
        "penalty_rate_per_day_inr": 15_000.0,
        "switching_or_tooling_cost_inr": 120_000.0,  # One-time tooling re-calibration fee
        "requires_manual_review": False,
        "source_clause_ref": "ElectroMotion Dual-Sourcing Framework Agreement Section 7.1 & Tooling Annex C",
    },
    "SUP-1001": {
        "contract_id": "CNT-BHARAT-2024-11",
        "supplier_id": "SUP-1001",
        "supplier_name": "Bharat Precision Dynamics",
        "is_approved_vendor": True,
        "alternate_sourcing_permitted": True,
        "moq_units": 250.0,
        "capacity_ceiling_units": 20_000.0,
        "standard_lead_time_days": 12.0,
        "expedite_lead_time_days": 5.0,
        "expedite_premium_rate": 0.30,
        "unit_purchase_price_inr": 2_400.0,
        "penalty_rate_per_day_inr": 10_000.0,
        "switching_or_tooling_cost_inr": 50_000.0,
        "requires_manual_review": False,
        "source_clause_ref": "BPD Framework Agreement 2024 Clause 11",
    },
}


def extract_contract_constraints(
    supplier_id: str,
    override: Optional[ContractConstraints] = None,
) -> ContractConstraints:
    """
    Deterministically retrieve and validate structured contract constraints.
    Falls back to a flagged generic contract if supplier is not registered.
    """
    if override:
        is_valid, reasons = validate_contract_constraints(override)
        if not is_valid:
            override.requires_manual_review = True
            override.validation_status = "FLAGGED_FOR_MANUAL_REVIEW"
        return override

    raw = CONTRACT_REGISTRY.get(supplier_id)
    if not raw:
        # Unknown supplier contract: enforce honest fallback with manual review requirement
        return ContractConstraints(
            contract_id=f"CNT-UNVERIFIED-{supplier_id}",
            supplier_id=supplier_id,
            supplier_name=f"Supplier {supplier_id}",
            is_approved_vendor=False,
            alternate_sourcing_permitted=False,
            moq_units=500.0,
            capacity_ceiling_units=10_000.0,
            standard_lead_time_days=14.0,
            expedite_lead_time_days=7.0,
            expedite_premium_rate=0.40,
            unit_purchase_price_inr=3_000.0,
            penalty_rate_per_day_inr=10_000.0,
            switching_or_tooling_cost_inr=200_000.0,
            requires_manual_review=True,
            validation_status="FLAGGED_FOR_MANUAL_REVIEW",
            source_clause_ref="No verified contract on file. Flagged for Category Manager review.",
        )

    constraints = ContractConstraints(**raw)
    is_valid, _ = validate_contract_constraints(constraints)
    if not is_valid:
        constraints.requires_manual_review = True
        constraints.validation_status = "FLAGGED_FOR_MANUAL_REVIEW"

    return constraints


def validate_contract_constraints(c: ContractConstraints) -> Tuple[bool, List[str]]:
    """
    Validate contractual bounds and consistency before feeding the optimization solver.
    """
    errors: List[str] = []

    if c.moq_units < 0:
        errors.append("MOQ cannot be negative.")
    if c.capacity_ceiling_units <= 0:
        errors.append("Capacity ceiling must be positive.")
    if c.moq_units > c.capacity_ceiling_units:
        errors.append("MOQ exceeds total supplier capacity ceiling.")
    if c.expedite_lead_time_days > c.standard_lead_time_days:
        errors.append("Expedite lead time cannot exceed standard lead time.")
    if c.expedite_premium_rate < 0.0 or c.expedite_premium_rate > 2.0:
        errors.append("Expedite premium rate must be between 0.0 and 2.0 (0% to 200%).")
    if c.unit_purchase_price_inr <= 0:
        errors.append("Unit purchase price must be positive.")

    return len(errors) == 0, errors
