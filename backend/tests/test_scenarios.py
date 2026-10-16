"""Tests for Sprint 5: Scenario Simulation, Structured Constraints, and Optimisation Studio."""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.scenario import (
    ContractConstraints,
    ScenarioGenerationRequest,
    ScenarioOptimizationRequest,
)
from app.services.optimizer.constraints import (
    extract_contract_constraints,
    validate_contract_constraints,
)
from app.services.optimizer.service import scenario_service
from scripts.generate_synthetic_data import generate

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "generated"

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def ensure_dataset():
    """Ensure small scale synthetic dataset exists."""
    if not (DATA_DIR / "supplier.csv").exists():
        generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")


def test_structured_contract_constraint_extraction_and_validation():
    """Verify deterministic schema extraction and manual review fallback for unverified suppliers."""
    # 1. Flagship supplier SUP-1047
    apex_contract = extract_contract_constraints("SUP-1047")
    assert apex_contract.supplier_id == "SUP-1047"
    assert apex_contract.is_approved_vendor is True
    assert apex_contract.alternate_sourcing_permitted is True
    assert apex_contract.moq_units == 500.0
    assert apex_contract.requires_manual_review is False
    assert apex_contract.validation_status == "VALIDATED"

    # 2. Alternate supplier SUP-1012
    electro_contract = extract_contract_constraints("SUP-1012")
    assert electro_contract.supplier_id == "SUP-1012"
    assert electro_contract.is_approved_vendor is True
    assert electro_contract.switching_or_tooling_cost_inr == 120_000.0
    assert electro_contract.moq_units == 1_000.0

    # 3. Unknown supplier: must flag for manual review
    unknown_contract = extract_contract_constraints("SUP-UNKNOWN-999")
    assert unknown_contract.requires_manual_review is True
    assert unknown_contract.validation_status == "FLAGGED_FOR_MANUAL_REVIEW"
    assert unknown_contract.is_approved_vendor is False

    # 4. Validation logic for invalid bounds
    invalid_contract = ContractConstraints(
        contract_id="CNT-BAD",
        supplier_id="SUP-BAD",
        supplier_name="Bad Supplier",
        moq_units=50_000.0,
        capacity_ceiling_units=10_000.0,  # MOQ > capacity
        standard_lead_time_days=10.0,
        expedite_lead_time_days=15.0,  # Expedite > standard
        expedite_premium_rate=0.25,
        unit_purchase_price_inr=100.0,
    )
    is_valid, errors = validate_contract_constraints(invalid_contract)
    assert is_valid is False
    assert any("MOQ exceeds" in err for err in errors)
    assert any("Expedite lead time cannot exceed" in err for err in errors)


def test_generate_four_canonical_scenarios_for_sup_1047():
    """Verify generation of minimum 4 scenarios (A, B, C, D) with objective cost reconciliation."""
    req = ScenarioGenerationRequest(
        supplier_id="SUP-1047",
        alternate_supplier_id="SUP-1012",
        disruption_lead_time_days=14.0,
        stockout_probability=0.85,
        as_of_date="2026-09-30",
    )
    res = scenario_service.generate_scenarios(req, DATA_DIR)

    assert res.supplier_id == "SUP-1047"
    assert len(res.scenarios) == 4

    scen_ids = [s.scenario_id for s in res.scenarios]
    assert scen_ids == ["SCN-A", "SCN-B", "SCN-C", "SCN-D"]

    scn_a = res.scenarios[0]
    scn_b = res.scenarios[1]
    scn_c = res.scenarios[2]
    scn_d = res.scenarios[3]

    # Scenario A: Do Nothing counterfactual baseline
    assert scn_a.scenario_type == "DO_NOTHING"
    assert scn_a.total_mitigation_cost_inr == 0.0
    assert scn_a.net_avoided_loss_inr == 0.0
    assert scn_a.residual_revenue_exposure_inr == res.baseline_revenue_exposure_inr

    # Scenario D: Hybrid must deliver highest net avoided loss and positive ROI
    assert scn_d.scenario_type == "HYBRID"
    assert scn_d.is_feasible is True
    assert scn_d.net_avoided_loss_inr > 0.0
    assert scn_d.roi_percentage > 0.0
    assert scn_d.runway_gain_days > 0.0
    assert scn_d.projected_service_level > scn_a.projected_service_level

    # Objective Cost Reconciliation across all scenarios
    for s in res.scenarios:
        expected_total = round(
            s.expedite_cost_inr
            + s.switching_cost_inr
            + s.buffer_transfer_cost_inr
            + s.delta_purchase_cost_inr,
            2,
        )
        assert round(s.total_mitigation_cost_inr, 2) == expected_total

    # Recommended scenario must be SCN-D
    assert res.recommended_scenario_id == "SCN-D"


def test_scenario_b_alternate_supplier_constraints():
    """Verify SCN-B respects MOQ, alternate capacity, and tooling fees."""
    req = ScenarioGenerationRequest(
        supplier_id="SUP-1047",
        alternate_supplier_id="SUP-1012",
        disruption_lead_time_days=14.0,
    )
    res = scenario_service.generate_scenarios(req, DATA_DIR)
    scn_b = next(s for s in res.scenarios if s.scenario_id == "SCN-B")

    assert scn_b.is_feasible is True
    assert scn_b.switching_cost_inr == 120_000.0  # Tooling recalibration fee
    assert scn_b.delta_purchase_cost_inr >= 0.0
    assert len(scn_b.actions) == 1
    assert scn_b.actions[0].action_type == "ALTERNATE_ALLOCATION"
    assert scn_b.actions[0].allocated_units >= 1_000.0  # Contractual MOQ


def test_scenario_c_expedite_and_buffer_transfer():
    """Verify SCN-C validates speed vs freight cost without switching vendors."""
    req = ScenarioGenerationRequest(
        supplier_id="SUP-1047",
        disruption_lead_time_days=14.0,
    )
    res = scenario_service.generate_scenarios(req, DATA_DIR)
    scn_c = next(s for s in res.scenarios if s.scenario_id == "SCN-C")

    assert scn_c.is_feasible is True
    assert scn_c.expedite_cost_inr > 0.0
    assert scn_c.buffer_transfer_cost_inr > 0.0
    assert scn_c.switching_cost_inr == 0.0  # No alternate supplier
    assert scn_c.runway_gain_days >= 5.0


def test_infeasibility_handling_explicit():
    """When contractual constraints are breached, solver must flag infeasibility with reasons."""
    # Prohibit dual sourcing via override
    prohibited_contract = ContractConstraints(
        contract_id="CNT-PROHIBITED",
        supplier_id="SUP-1012",
        supplier_name="Restricted Alternate",
        is_approved_vendor=True,
        alternate_sourcing_permitted=False,  # Prohibited!
        moq_units=500.0,
        capacity_ceiling_units=20_000.0,
        standard_lead_time_days=10.0,
        expedite_lead_time_days=4.0,
        expedite_premium_rate=0.20,
        unit_purchase_price_inr=3000.0,
    )

    req = ScenarioGenerationRequest(
        supplier_id="SUP-1047",
        alternate_supplier_id="SUP-1012",
        contract_override=prohibited_contract,
    )
    # Primary contract override with non-permitted dual sourcing
    res = scenario_service.generate_scenarios(req, DATA_DIR)
    assert res.scenarios is not None

    # Test unapproved vendor for SCN-B
    unapproved_alt = ContractConstraints(
        contract_id="CNT-UNAPPROVED",
        supplier_id="SUP-UNAPPROVED",
        supplier_name="Unapproved Vendor",
        is_approved_vendor=False,  # Unapproved!
        alternate_sourcing_permitted=True,
        moq_units=500.0,
        capacity_ceiling_units=50_000.0,
        standard_lead_time_days=10.0,
        expedite_lead_time_days=4.0,
        expedite_premium_rate=0.20,
        unit_purchase_price_inr=3000.0,
    )
    from app.services.optimizer.solver import evaluate_scenario_b_alternate_supplier
    from app.services.impact_engine import traverse_supplier_network
    report = traverse_supplier_network("SUP-1047", DATA_DIR)
    primary = extract_contract_constraints("SUP-1047")
    scn_infeasible = evaluate_scenario_b_alternate_supplier(report, primary, unapproved_alt)

    assert scn_infeasible.is_feasible is False
    assert len(scn_infeasible.infeasibility_reasons) > 0
    assert any("not an approved vendor" in r for r in scn_infeasible.infeasibility_reasons)


def test_scenario_optimisation_ranking_and_sensitivity():
    """Verify optimisation ranking by net avoided loss and sensitivity stability."""
    opt_req = ScenarioOptimizationRequest(
        supplier_id="SUP-1047",
        min_acceptable_service_level=0.80,
        max_mitigation_budget_inr=25_000_000.0,  # 2.5 Cr budget allows SCN-D (1.84 Cr)
    )
    opt_res = scenario_service.optimize_scenarios(opt_req, DATA_DIR)

    assert opt_res.supplier_id == "SUP-1047"
    assert len(opt_res.ranked_scenarios) == 4
    assert opt_res.optimal_scenario.scenario_id == "SCN-D"

    # Test tight budget cap (50 Lakhs): SCN-D exceeds budget, SCN-B (30 Lakhs) becomes optimal feasible
    tight_req = ScenarioOptimizationRequest(
        supplier_id="SUP-1047",
        min_acceptable_service_level=0.80,
        max_mitigation_budget_inr=5_000_000.0,  # 50 Lakh cap
    )
    tight_res = scenario_service.optimize_scenarios(tight_req, DATA_DIR)
    assert tight_res.optimal_scenario.scenario_id == "SCN-B"
    assert tight_res.infeasible_scenarios_count >= 1

    # Sensitivity analysis
    assert len(opt_res.sensitivity_analysis) >= 6
    for item in opt_res.sensitivity_analysis:
        assert item.parameter_name in {"disruption_lead_time_days", "stockout_probability"}
        assert item.recommended_scenario_id == "SCN-D"
        assert item.is_feasible is True


def test_scenarios_api_endpoints():
    """Verify REST endpoints for /scenarios/generate, /scenarios/optimise, and constraints."""
    # 1. POST /api/v1/scenarios/generate
    res_gen = client.post(
        "/api/v1/scenarios/generate",
        json={"supplier_id": "SUP-1047", "disruption_lead_time_days": 14.0},
    )
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["supplier_id"] == "SUP-1047"
    assert len(gen_data["scenarios"]) == 4
    assert gen_data["recommended_scenario_id"] == "SCN-D"

    # 2. POST /api/v1/scenarios/optimise
    res_opt = client.post(
        "/api/v1/scenarios/optimise",
        json={
            "supplier_id": "SUP-1047",
            "min_acceptable_service_level": 0.85,
            "max_mitigation_budget_inr": 10_000_000.0,
        },
    )
    assert res_opt.status_code == 200
    opt_data = res_opt.json()
    assert opt_data["optimal_scenario"]["scenario_id"] == "SCN-D"
    assert len(opt_data["sensitivity_analysis"]) > 0

    # 3. GET /api/v1/scenarios/constraints/SUP-1047
    res_cnt = client.get("/api/v1/scenarios/constraints/SUP-1047")
    assert res_cnt.status_code == 200
    cnt_data = res_cnt.json()
    assert cnt_data["supplier_id"] == "SUP-1047"
    assert cnt_data["moq_units"] == 500.0
    assert cnt_data["is_approved_vendor"] is True
