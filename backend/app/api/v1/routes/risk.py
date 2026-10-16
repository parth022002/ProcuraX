"""Supplier risk scoring endpoints.

Exposes:
- Governed 0-100 risk score with explainable top drivers
- ML disruption probability P(disruption)
- Model card metadata with calibration and performance metrics
"""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, status
import pandas as pd

from app.schemas.risk import ModelCardResponse, RiskDriverSchema, RiskScoreRequest, RiskScoreResponse
from app.services.risk_model.features import compute_supplier_features
from app.services.risk_model.model import MODEL_VERSION, SupplierRiskModel, train_and_register_baseline
from app.services.risk_model.scoring import FORMULA_VERSION, calculate_governed_risk_score

router = APIRouter(tags=["risk"])

ROOT = Path(__file__).resolve().parents[5]
DATA_DIR = ROOT / "data" / "generated"
MODEL_DIR = ROOT / "models" / "registry"

_MODEL_CACHE: SupplierRiskModel | None = None


def get_model() -> SupplierRiskModel:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    model_path = MODEL_DIR / "logistic_model.pkl"
    if model_path.exists():
        _MODEL_CACHE = SupplierRiskModel.load(model_path)
    else:
        # Train baseline if not yet registered
        if not (DATA_DIR / "supplier.csv").exists():
            from scripts.generate_synthetic_data import generate
            generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")
        _MODEL_CACHE, _ = train_and_register_baseline(DATA_DIR, output_model_dir=MODEL_DIR, model_type="logistic")

    return _MODEL_CACHE


@router.get("/risk/model-card", response_model=ModelCardResponse)
def get_model_card():
    """Retrieve the model card for the current disruption baseline."""
    card_path = MODEL_DIR / "logistic_model_card.json"
    if not card_path.exists():
        get_model()  # Triggers training and card creation

    if card_path.exists():
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
        return ModelCardResponse(**card_data)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model card not found.")


@router.post("/risk/score", response_model=RiskScoreResponse)
def compute_risk_score(request: RiskScoreRequest):
    """Compute governed risk score (0-100) and ML disruption probability for a supplier."""
    supplier_id = request.supplier_id
    as_of = pd.Timestamp(request.as_of_date or "2026-09-30").normalize()

    # Obtain feature dictionary
    if request.custom_features:
        features = request.custom_features
    else:
        if not (DATA_DIR / "supplier.csv").exists():
            from scripts.generate_synthetic_data import generate
            generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")

        suppliers_df = pd.read_csv(DATA_DIR / "supplier.csv")
        quality_df = pd.read_csv(DATA_DIR / "quality.csv")
        capacity_df = pd.read_csv(DATA_DIR / "capacity.csv")
        signals_df = pd.read_csv(DATA_DIR / "external_event.csv")

        try:
            features = compute_supplier_features(
                supplier_id=supplier_id,
                as_of=as_of,
                suppliers_df=suppliers_df,
                performance_df=quality_df,
                capacity_df=capacity_df,
                signals_df=signals_df,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # ML disruption probability from model
    model = get_model()
    ml_prob = model.predict_single(features)

    # Governed 0-100 score formulation
    governed = calculate_governed_risk_score(
        supplier_id=supplier_id,
        features=features,
        ml_probability=ml_prob,
    )

    drivers_schema = [
        RiskDriverSchema(
            name=d.name,
            contribution_points=d.contribution_points,
            description=d.description,
            direction=d.direction,
        )
        for d in governed.driver_breakdown
    ]

    return RiskScoreResponse(
        supplier_id=supplier_id,
        governed_risk_score=governed.governed_score,
        risk_level=governed.risk_level,
        ml_disruption_probability=ml_prob,
        top_drivers=governed.top_drivers,
        driver_breakdown=drivers_schema,
        formula_version=FORMULA_VERSION,
        model_version=MODEL_VERSION,
        metadata={"features": features, **governed.metadata},
    )


@router.get("/risk/score", response_model=RiskScoreResponse)
def get_risk_score(
    supplier_id: str = Query(..., description="Unique supplier identifier (e.g. SUP-1047)"),
    as_of_date: str | None = Query(None, description="Prediction cutoff date (YYYY-MM-DD)"),
):
    """Retrieve governed risk score and ML disruption probability for a supplier via GET."""
    req = RiskScoreRequest(supplier_id=supplier_id, as_of_date=as_of_date)
    return compute_risk_score(req)
