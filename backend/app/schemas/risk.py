"""Risk scoring and model card API schemas."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class RiskDriverSchema(BaseModel):
    name: str
    contribution_points: float
    description: str
    direction: str


class RiskScoreRequest(BaseModel):
    supplier_id: str
    as_of_date: str | None = None
    custom_features: dict[str, float] | None = None


class RiskScoreResponse(BaseModel):
    supplier_id: str
    governed_risk_score: float = Field(..., ge=0, le=100, description="Governed multidimensional operational risk score (0-100)")
    risk_level: str = Field(..., description="'Low' | 'Medium' | 'High' | 'Critical'")
    ml_disruption_probability: float = Field(..., ge=0.0, le=1.0, description="Binary 30-day disruption likelihood P(disruption)")
    top_drivers: list[str]
    driver_breakdown: list[RiskDriverSchema]
    formula_version: str
    model_version: str
    distinction_note: str = (
        "Governed risk score (0-100) measures multidimensional operational risk; "
        "ML probability measures binary 30-day disruption likelihood. They are kept separate by system policy."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelCardResponse(BaseModel):
    model_name: str
    model_version: str
    target_definition: str
    prediction_horizon: str
    training_cutoff_date: str
    feature_list: list[str]
    held_out_flagship: str
    metrics: dict[str, Any]
    feature_importances: dict[str, float]
    provenance: str = "SYNTHETIC"
