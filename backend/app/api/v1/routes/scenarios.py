"""API routes for Sprint 5: Mitigation Scenario Simulation and Optimisation Studio."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from app.schemas.scenario import (
    ContractConstraints,
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
    ScenarioOptimizationRequest,
    ScenarioOptimizationResponse,
)
from app.services.optimizer.service import scenario_service

router = APIRouter(tags=["scenarios"])

ROOT_DIR = Path(__file__).resolve().parents[5]
DATA_DIR = ROOT_DIR / "data" / "generated"


@router.post(
    "/scenarios/generate",
    summary="Generate candidate mitigation scenarios (A, B, C, D)",
    response_model=ScenarioGenerationResponse,
)
def generate_scenarios_endpoint(request: ScenarioGenerationRequest):
    """
    Generate 4 canonical mitigation options:
    A (Do Nothing), B (Alternate Supplier), C (Expedite/Buffer), D (Hybrid).
    Calculates cost breakdown, net avoided loss, runway gains, and ROI.
    """
    try:
        return scenario_service.generate_scenarios(request, DATA_DIR)
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required data foundation missing: {fnf}",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


@router.post(
    "/scenarios/optimise",
    summary="Rank feasible mitigation scenarios subject to service and budget constraints",
    response_model=ScenarioOptimizationResponse,
)
def optimise_scenarios_endpoint(request: ScenarioOptimizationRequest):
    """
    Filter and rank feasible mitigation candidates against operational constraints.
    Infeasibility is made explicit; includes sensitivity analysis across lead time and probability.
    """
    try:
        return scenario_service.optimize_scenarios(request, DATA_DIR)
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required data foundation missing: {fnf}",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


@router.get(
    "/scenarios/constraints/{supplier_id}",
    summary="Get validated contract and policy constraints for a supplier",
    response_model=ContractConstraints,
)
def get_supplier_constraints_endpoint(supplier_id: str):
    """Retrieve structured, schema-validated MOQ, capacity, lead time, and pricing constraints."""
    return scenario_service.get_constraints(supplier_id)
