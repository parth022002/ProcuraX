"""Pydantic schemas for Sprint 4: Deterministic Impact Engine and Network Dependency Traversal."""
from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class DirectImpactInputs(BaseModel):
    """Direct parameters for single-node what-if calculation."""
    on_hand_units: float = Field(..., ge=0, description="Current stock on hand in physical units")
    average_daily_consumption: float = Field(..., ge=0, description="Average daily burn rate / consumption in units")
    safety_stock_units: float = Field(0.0, ge=0, description="Buffer / safety stock threshold")
    units_at_risk: float = Field(..., ge=0, description="Units demanded during the disruption window that cannot be fulfilled")
    contribution_margin_per_unit_inr: float = Field(..., ge=0, description="Contribution margin per unit in INR (revenue minus variable costs)")
    stockout_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability of supply interruption (from risk engine)")


class SkuImpactSummary(BaseModel):
    """Per-SKU impact breakdown."""
    sku_id: str
    family: str
    criticality: int
    plant: str
    on_hand_units: float
    safety_stock_units: float
    average_daily_consumption: float
    runway_days: float
    buffer_penetration_days: float
    projected_stockout_date: Optional[str]
    open_po_units: float
    units_at_risk: float
    unit_contribution_margin_inr: float
    revenue_exposure_inr: float


class PlantImpactSummary(BaseModel):
    """Per-Plant aggregate vulnerability."""
    plant: str
    affected_sku_count: int
    critical_sku_count: int
    min_runway_days: float
    average_runway_days: float
    total_units_at_risk: float
    total_revenue_exposure_inr: float
    downtime_risk_level: str


class DependencyGraphNode(BaseModel):
    """Node in the multi-tier supply network traversal."""
    id: str
    label: str
    node_type: str  # "SUPPLIER", "CATEGORY", "SKU", "PLANT"
    criticality: Optional[int] = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class DependencyGraphEdge(BaseModel):
    """Directed edge in the supply network dependency graph."""
    source: str
    target: str
    relation: str  # "SUPPLIES", "INCORPORATES", "STOCKED_AT"
    weight_or_units: Optional[float] = None


class NetworkDependencyGraph(BaseModel):
    """Topological graph showing Supplier -> Component/Category -> SKU -> Assembly Plant."""
    nodes: List[DependencyGraphNode]
    edges: List[DependencyGraphEdge]


class ImpactCalculationRequest(BaseModel):
    """Request payload for impact calculation."""
    supplier_id: Optional[str] = Field("SUP-1047", description="Target supplier to traverse in network")
    disruption_lead_time_days: float = Field(14.0, ge=1.0, description="Simulated duration of supply stoppage in days")
    stockout_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override stockout probability; if None, derived from risk baseline")
    as_of_date: Optional[str] = Field("2026-09-30", description="Evaluation anchor date (ISO-8601)")
    custom_inputs: Optional[DirectImpactInputs] = Field(None, description="Direct standalone inputs for what-if calculator")


class DirectImpactResult(BaseModel):
    """Result of direct what-if calculation."""
    inventory_runway_days: float
    buffer_penetration_days: float
    revenue_exposure_inr: float
    formula_version: str
    assumptions: List[str]


class ImpactReportResponse(BaseModel):
    """Comprehensive deterministic impact report for a supplier and its supply network."""
    supplier_id: str
    supplier_name: str
    as_of_date: str
    disruption_lead_time_days: float
    stockout_probability_used: float
    total_revenue_exposure_inr: float
    min_inventory_runway_days: float
    most_vulnerable_plant: str
    most_vulnerable_sku: str
    affected_sku_count: int
    affected_plants: List[str]
    sku_impacts: List[SkuImpactSummary]
    plant_impacts: List[PlantImpactSummary]
    dependency_graph: NetworkDependencyGraph
    priority_index: float
    formula_version: str
    assumptions: List[str]
    lineage: dict[str, str]
