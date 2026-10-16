"""API routes for Sprint 4: Deterministic Impact Engine and Supply Network Traversal."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.impact import (
    DirectImpactInputs,
    DirectImpactResult,
    ImpactCalculationRequest,
    ImpactReportResponse,
    NetworkDependencyGraph,
)
from app.services.impact_engine import (
    calculate_direct_whatif,
    traverse_supplier_network,
)

router = APIRouter(tags=["impact"])

ROOT_DIR = Path(__file__).resolve().parents[5]
DATA_DIR = ROOT_DIR / "data" / "generated"


@router.post(
    "/impact/calculate",
    summary="Calculate financial exposure and inventory runway",
    response_model=dict,
)
def calculate_impact_endpoint(request: ImpactCalculationRequest):
    """
    Calculate deterministic inventory runway, stockouts, and revenue-at-risk.
    Supports either direct what-if inputs or full multi-tier network traversal.
    """
    if request.custom_inputs:
        result = calculate_direct_whatif(request.custom_inputs)
        return {
            "mode": "direct_simulation",
            "result": result.model_dump(),
        }

    supplier_id = request.supplier_id or "SUP-1047"
    try:
        report = traverse_supplier_network(
            supplier_id=supplier_id,
            data_dir=DATA_DIR,
            disruption_lead_time_days=request.disruption_lead_time_days,
            stockout_probability=request.stockout_probability,
            as_of_date=request.as_of_date or "2026-09-30",
        )
        return {
            "mode": "network_traversal",
            "report": report.model_dump(),
        }
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supply network data tables not available: {fnf}",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


@router.get(
    "/impact/supplier/{supplier_id}",
    summary="Get full impact analysis report for a supplier",
    response_model=ImpactReportResponse,
)
def get_supplier_impact_report(
    supplier_id: str,
    disruption_days: float = Query(14.0, ge=1.0, description="Disruption lead time in days"),
    stockout_prob: Optional[float] = Query(None, ge=0.0, le=1.0, description="Override stockout probability"),
    as_of: str = Query("2026-09-30", description="As-of evaluation anchor date"),
):
    """Return deterministic multi-plant inventory runway, revenue at risk, and impact summaries."""
    try:
        return traverse_supplier_network(
            supplier_id=supplier_id,
            data_dir=DATA_DIR,
            disruption_lead_time_days=disruption_days,
            stockout_probability=stockout_prob,
            as_of_date=as_of,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data tables missing: {fnf}",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


@router.get(
    "/impact/network/{supplier_id}",
    summary="Get multi-level supply network dependency graph",
    response_model=NetworkDependencyGraph,
)
def get_supplier_network_graph(
    supplier_id: str,
    disruption_days: float = Query(14.0, ge=1.0),
    as_of: str = Query("2026-09-30"),
):
    """Return topological graph: Supplier -> Category -> SKUs -> Assembly Plants."""
    try:
        report = traverse_supplier_network(
            supplier_id=supplier_id,
            data_dir=DATA_DIR,
            disruption_lead_time_days=disruption_days,
            as_of_date=as_of,
        )
        return report.dependency_graph
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to generate dependency graph: {exc}",
        )
