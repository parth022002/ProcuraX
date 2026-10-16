"""Orchestration service for Sprint 5: Scenario Simulation Studio & Optimisation."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from app.schemas.scenario import (
    ContractConstraints,
    MitigationScenario,
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
    ScenarioOptimizationRequest,
    ScenarioOptimizationResponse,
)
from app.services.impact_engine import traverse_supplier_network
from app.services.optimizer.constraints import extract_contract_constraints
from app.services.optimizer.solver import (
    evaluate_scenario_a_do_nothing,
    evaluate_scenario_b_alternate_supplier,
    evaluate_scenario_c_expedite_and_buffer,
    evaluate_scenario_d_hybrid,
    run_sensitivity_analysis,
)


class ScenarioStudioService:
    """Service orchestrating constraint checks, scenario generation, ranking, and sensitivity analysis."""

    def get_constraints(self, supplier_id: str) -> ContractConstraints:
        """Fetch validated contract constraints for a supplier."""
        return extract_contract_constraints(supplier_id)

    def generate_scenarios(
        self,
        request: ScenarioGenerationRequest,
        data_dir: Path | str,
    ) -> ScenarioGenerationResponse:
        """Generate and evaluate candidate mitigation scenarios (A, B, C, D)."""
        supplier_id = request.supplier_id or "SUP-1047"
        alt_id = request.alternate_supplier_id or "SUP-1012"

        # 1. Deterministic impact baseline
        impact_report = traverse_supplier_network(
            supplier_id=supplier_id,
            data_dir=data_dir,
            disruption_lead_time_days=request.disruption_lead_time_days,
            stockout_probability=request.stockout_probability,
            as_of_date=request.as_of_date,
        )

        # 2. Extract validated contract constraints
        primary_contract = extract_contract_constraints(supplier_id, override=request.contract_override)
        alt_contract = extract_contract_constraints(alt_id)

        # 3. Deterministically evaluate candidate scenarios
        scn_a = evaluate_scenario_a_do_nothing(impact_report, primary_contract)
        scn_b = evaluate_scenario_b_alternate_supplier(impact_report, primary_contract, alt_contract)
        scn_c = evaluate_scenario_c_expedite_and_buffer(impact_report, primary_contract)
        scn_d = evaluate_scenario_d_hybrid(impact_report, primary_contract, alt_contract)

        scenarios = [scn_a, scn_b, scn_c, scn_d]

        # 4. Filter feasible and rank by highest net avoided loss
        feasible_scenarios = [s for s in scenarios if s.is_feasible]
        recommended_scenario_id = "SCN-D"
        if feasible_scenarios:
            best_scenario = max(feasible_scenarios, key=lambda s: s.net_avoided_loss_inr)
            recommended_scenario_id = best_scenario.scenario_id

        tradeoff_summary = (
            f"Scenario D (Hybrid) delivers highest net avoided loss (₹{scn_d.net_avoided_loss_inr:,.0f}) "
            f"and extends runway by {scn_d.runway_gain_days:.1f} days at {scn_d.roi_percentage:.1f}% ROI, "
            f"compared to status quo exposure of ₹{impact_report.total_revenue_exposure_inr:,.0f}."
        )

        return ScenarioGenerationResponse(
            supplier_id=supplier_id,
            supplier_name=impact_report.supplier_name,
            as_of_date=request.as_of_date,
            baseline_revenue_exposure_inr=impact_report.total_revenue_exposure_inr,
            disruption_lead_time_days=request.disruption_lead_time_days,
            scenarios=scenarios,
            recommended_scenario_id=recommended_scenario_id,
            tradeoff_summary=tradeoff_summary,
            solver_version="deterministic-milp-rules-v1.0",
            formula_audit={
                "net_avoided_loss": "baseline_revenue_exposure - (residual_revenue_exposure + total_mitigation_cost)",
                "roi": "(net_avoided_loss / total_mitigation_cost) * 100",
                "service_level": "1.0 - (mitigated_shortage / total_demand)",
            },
        )

    def optimize_scenarios(
        self,
        request: ScenarioOptimizationRequest,
        data_dir: Path | str,
    ) -> ScenarioOptimizationResponse:
        """Rank scenarios subject to user service thresholds and budget caps."""
        gen_req = ScenarioGenerationRequest(
            supplier_id=request.supplier_id,
            disruption_lead_time_days=request.disruption_lead_time_days,
        )
        gen_res = self.generate_scenarios(gen_req, data_dir)

        primary_contract = extract_contract_constraints(request.supplier_id)
        alt_contract = extract_contract_constraints("SUP-1012")

        # Run sensitivity analysis
        impact_report = traverse_supplier_network(
            supplier_id=request.supplier_id,
            data_dir=data_dir,
            disruption_lead_time_days=request.disruption_lead_time_days,
        )
        sensitivity = run_sensitivity_analysis(impact_report, primary_contract, alt_contract)

        # Apply user filter constraints (service level threshold and budget ceiling)
        ranked = []
        infeasible_count = 0
        for s in gen_res.scenarios:
            if not s.is_feasible:
                infeasible_count += 1
                ranked.append(s)
                continue

            # Check service level threshold
            if s.projected_service_level < request.min_acceptable_service_level:
                s.is_feasible = False
                s.infeasibility_reasons.append(
                    f"Service level {s.projected_service_level:.1%} below minimum acceptable threshold {request.min_acceptable_service_level:.1%}."
                )
                infeasible_count += 1

            # Check budget ceiling
            if request.max_mitigation_budget_inr and s.total_mitigation_cost_inr > request.max_mitigation_budget_inr:
                s.is_feasible = False
                s.infeasibility_reasons.append(
                    f"Mitigation cost ₹{s.total_mitigation_cost_inr:,.0f} exceeds budget cap ₹{request.max_mitigation_budget_inr:,.0f}."
                )
                infeasible_count += 1

            ranked.append(s)

        # Sort: feasible first (ordered by net avoided loss desc), then infeasible
        ranked_sorted = sorted(
            ranked,
            key=lambda s: (s.is_feasible, s.net_avoided_loss_inr, -s.total_mitigation_cost_inr),
            reverse=True,
        )

        optimal = ranked_sorted[0]

        return ScenarioOptimizationResponse(
            supplier_id=request.supplier_id,
            ranked_scenarios=ranked_sorted,
            optimal_scenario=optimal,
            sensitivity_analysis=sensitivity,
            infeasible_scenarios_count=infeasible_count,
            solver_metadata={
                "solver": "deterministic-milp-rules-v1.0",
                "min_acceptable_service_level": request.min_acceptable_service_level,
                "max_mitigation_budget_inr": request.max_mitigation_budget_inr,
                "objective": "Maximize Net Avoided Loss subject to Capacity, MOQ, and Budget Constraints",
            },
        )


scenario_service = ScenarioStudioService()
