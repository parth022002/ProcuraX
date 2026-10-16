"""Pydantic schemas for Sprint 5: Scenario Simulation, Structured Constraints, and Optimisation."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContractConstraints(BaseModel):
    """Structured, schema-validated contract and policy constraints for a supplier."""
    contract_id: str
    supplier_id: str
    supplier_name: str
    is_approved_vendor: bool = True
    alternate_sourcing_permitted: bool = True
    moq_units: float = Field(0.0, ge=0.0, description="Minimum order quantity in units")
    capacity_ceiling_units: float = Field(100_000.0, ge=0.0, description="Maximum available capacity per period")
    standard_lead_time_days: float = Field(14.0, ge=1.0, description="Contractual standard delivery lead time")
    expedite_lead_time_days: float = Field(5.0, ge=1.0, description="Compressed lead time under expedite terms")
    expedite_premium_rate: float = Field(0.35, ge=0.0, le=2.0, description="Expedite surcharge (e.g. 0.35 = +35%)")
    unit_purchase_price_inr: float = Field(2_500.0, ge=0.0, description="Contracted unit purchase price in INR")
    penalty_rate_per_day_inr: float = Field(10_000.0, ge=0.0, description="Contractual delay penalty per day")
    switching_or_tooling_cost_inr: float = Field(0.0, ge=0.0, description="One-time qualification / tooling fee")
    requires_manual_review: bool = False
    validation_status: str = "VALIDATED"  # "VALIDATED", "FLAGGED_FOR_MANUAL_REVIEW"
    source_clause_ref: Optional[str] = "Master Supply Agreement (MSA) Section 4.2 & Schedule B"


class ScenarioAction(BaseModel):
    """Discrete operational action within a mitigation scenario."""
    action_type: str  # "EXPEDITE", "ALTERNATE_ALLOCATION", "BUFFER_TRANSFER", "DO_NOTHING"
    description: str
    allocated_units: float = Field(0.0, ge=0.0)
    source_entity: Optional[str] = None
    target_entity: Optional[str] = None
    unit_cost_inr: float = Field(0.0, ge=0.0)
    action_cost_inr: float = Field(0.0, ge=0.0)


class MitigationScenario(BaseModel):
    """Evaluated mitigation scenario candidate."""
    scenario_id: str  # "SCN-A", "SCN-B", "SCN-C", "SCN-D"
    name: str
    description: str
    scenario_type: str  # "DO_NOTHING", "ALTERNATE_SUPPLIER", "EXPEDITE_BUFFER", "HYBRID"
    is_feasible: bool
    infeasibility_reasons: List[str] = Field(default_factory=list)
    actions: List[ScenarioAction] = Field(default_factory=list)

    # Cost breakdown (INR)
    expedite_cost_inr: float = 0.0
    switching_cost_inr: float = 0.0
    buffer_transfer_cost_inr: float = 0.0
    delta_purchase_cost_inr: float = 0.0
    total_mitigation_cost_inr: float = 0.0

    # Operational outcome metrics
    baseline_revenue_exposure_inr: float = 0.0
    residual_revenue_exposure_inr: float = 0.0
    net_avoided_loss_inr: float = 0.0
    roi_percentage: float = 0.0
    runway_gain_days: float = 0.0
    projected_service_level: float = Field(0.0, ge=0.0, le=1.0)
    recovery_time_days: float = 0.0

    # Governance & compliance
    requires_executive_approval: bool = False
    approval_role_required: str = "SUPPLY_CHAIN_PLANNER"
    constraint_compliance_log: List[str] = Field(default_factory=list)


class ScenarioGenerationRequest(BaseModel):
    """Request payload to generate and evaluate mitigation candidates."""
    supplier_id: str = Field("SUP-1047", description="Target disrupted supplier")
    alternate_supplier_id: Optional[str] = Field("SUP-1012", description="Backup supplier (ElectroMotion Systems)")
    disruption_lead_time_days: float = Field(14.0, ge=1.0)
    stockout_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    as_of_date: str = Field("2026-09-30")
    custom_budget_inr: Optional[float] = Field(None, ge=0.0)
    contract_override: Optional[ContractConstraints] = None


class ScenarioGenerationResponse(BaseModel):
    """Output containing candidate scenarios and trade-off comparison."""
    supplier_id: str
    supplier_name: str
    as_of_date: str
    baseline_revenue_exposure_inr: float
    disruption_lead_time_days: float
    scenarios: List[MitigationScenario]
    recommended_scenario_id: str
    tradeoff_summary: str
    solver_version: str = "deterministic-milp-rules-v1.0"
    formula_audit: Dict[str, str] = Field(default_factory=dict)


class ScenarioOptimizationRequest(BaseModel):
    """Request to rank and select optimal scenario subject to operational thresholds."""
    supplier_id: str = Field("SUP-1047")
    min_acceptable_service_level: float = Field(0.85, ge=0.5, le=1.0)
    max_mitigation_budget_inr: Optional[float] = Field(None, ge=0.0)
    disruption_lead_time_days: float = Field(14.0, ge=1.0)


class ScenarioSensitivityItem(BaseModel):
    """Sensitivity analysis point changing a key parameter."""
    parameter_name: str
    parameter_value: Any
    recommended_scenario_id: str
    net_avoided_loss_inr: float
    is_feasible: bool


class ScenarioOptimizationResponse(BaseModel):
    """Ranked scenarios with sensitivity analysis."""
    supplier_id: str
    ranked_scenarios: List[MitigationScenario]
    optimal_scenario: MitigationScenario
    sensitivity_analysis: List[ScenarioSensitivityItem]
    infeasible_scenarios_count: int
    solver_metadata: Dict[str, Any]
