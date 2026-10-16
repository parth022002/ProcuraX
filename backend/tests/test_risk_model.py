"""Tests for Sprint 2: Supplier Risk Baseline Model, Governed Scoring, and API Endpoints."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.risk_model.features import compute_supplier_features, build_dataset_slices
from app.services.risk_model.model import SupplierRiskModel, train_and_register_baseline
from app.services.risk_model.scoring import calculate_governed_risk_score
from scripts.generate_synthetic_data import generate

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "generated"
MODEL_DIR = ROOT / "models" / "registry"

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def ensure_dataset():
    if not (DATA_DIR / "supplier.csv").exists():
        generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")


def test_build_dataset_slices_leakage_free():
    """Verify time-aware split and exclusion of SUP-1047 degradation window from training."""
    train_df, test_df = build_dataset_slices(DATA_DIR)

    assert not train_df.empty, "Train slice must not be empty"
    assert not test_df.empty, "Test slice must not be empty"
    assert "disrupted" in train_df.columns
    assert "disrupted" in test_df.columns

    # Assert that SUP-1047 degradation rows (>= 2026-07-02) are NEVER in train_df
    contaminated = train_df[
        (train_df["supplier_id"] == "SUP-1047")
        & (pd.to_datetime(train_df["period_date"]) >= pd.Timestamp("2026-07-02"))
    ]
    assert contaminated.empty, "SUP-1047 degradation window must be strictly excluded from training"


def test_baseline_risk_model_training_and_evaluation(tmp_path):
    """Train baseline model, check metrics, calibration (Brier score), and model card."""
    model, card = train_and_register_baseline(DATA_DIR, output_model_dir=tmp_path, model_type="logistic")

    assert model.is_fitted
    assert (tmp_path / "logistic_model.pkl").exists()
    assert (tmp_path / "logistic_model_card.json").exists()

    metrics = card.metrics
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "roc_auc" in metrics
    assert "brier_score" in metrics
    assert "expected_calibration_error" in metrics
    assert "calibration_curve" in metrics
    assert 0.0 <= metrics["brier_score"] <= 1.0, "Brier score must be a valid probability calibration metric"
    assert 0.0 <= metrics["expected_calibration_error"] <= 1.0, "ECE must be bounded in [0, 1]"
    assert metrics["roc_auc"] >= 0.50, "Classifier must beat random chance"
    assert card.held_out_flagship.startswith("SUP-1047")
    assert "quarantined" in card.limitations_and_ethics.lower()


def test_governed_risk_score_formulation():
    """Governed 0-100 score must respect bounds and reflect operational drivers."""
    healthy_features = {
        "otif_30d": 0.98,
        "otif_trend": 0.02,
        "lead_time_trend": -1.0,
        "defect_rate_30d": 0.005,
        "defect_rate_trend": -0.002,
        "capacity_utilisation_30d": 0.65,
        "recent_signal_severity": 0.0,
        "recent_signal_confidence": 0.0,
    }
    healthy_score = calculate_governed_risk_score("SUP-HEALTHY", healthy_features, ml_probability=0.08)
    assert 0.0 <= healthy_score.governed_score <= 40.0
    assert healthy_score.risk_level in {"Low", "Medium"}
    assert healthy_score.ml_probability == 0.08

    degraded_features = {
        "otif_30d": 0.62,
        "otif_trend": -0.25,
        "lead_time_trend": 14.0,
        "defect_rate_30d": 0.08,
        "defect_rate_trend": 0.04,
        "capacity_utilisation_30d": 0.96,
        "recent_signal_severity": 8.5,
        "recent_signal_confidence": 0.85,
    }
    degraded_score = calculate_governed_risk_score("SUP-1047", degraded_features, ml_probability=0.89)
    assert degraded_score.governed_score >= 60.0, "Severely degraded supplier must have high risk score"
    assert degraded_score.risk_level in {"High", "Critical"}
    assert degraded_score.ml_probability == 0.89
    assert len(degraded_score.top_drivers) >= 1
    assert "Delivery Reliability (OTIF)" in [d.name for d in degraded_score.driver_breakdown]


def test_risk_score_api_endpoints():
    """Test GET and POST /api/v1/risk/score and /api/v1/risk/model-card endpoints."""
    # 1. Model card endpoint
    res_card = client.get("/api/v1/risk/model-card")
    assert res_card.status_code == 200
    card = res_card.json()
    assert "model_name" in card
    assert "metrics" in card
    assert "feature_importances" in card

    # 2. Score endpoint for flagship supplier SUP-1047
    res_score = client.get("/api/v1/risk/score?supplier_id=SUP-1047&as_of_date=2026-09-30")
    assert res_score.status_code == 200
    body = res_score.json()
    assert body["supplier_id"] == "SUP-1047"
    assert 0 <= body["governed_risk_score"] <= 100
    assert 0.0 <= body["ml_disruption_probability"] <= 1.0
    assert len(body["top_drivers"]) >= 1
    assert "distinction_note" in body

    # 3. Post endpoint with custom features
    payload = {
        "supplier_id": "SUP-CUSTOM",
        "custom_features": {
            "otif_30d": 0.70,
            "otif_trend": -0.15,
            "lead_time_trend": 6.0,
            "defect_rate_30d": 0.05,
            "defect_rate_trend": 0.02,
            "capacity_utilisation_30d": 0.88,
            "recent_signal_severity": 5.0,
            "recent_signal_confidence": 0.7,
        },
    }
    res_post = client.post("/api/v1/risk/score", json=payload)
    assert res_post.status_code == 200
    post_body = res_post.json()
    assert post_body["supplier_id"] == "SUP-CUSTOM"
    assert post_body["governed_risk_score"] > 35.0

    # 4. Unknown supplier without custom features returns 404
    res_unknown = client.get("/api/v1/risk/score?supplier_id=SUP-NONEXISTENT")
    assert res_unknown.status_code == 404


def test_contamination_shield_rejects_flagship_degradation_window():
    """SupplierRiskModel.fit must fail immediately with ValueError if SUP-1047 degradation rows enter training."""
    from app.services.risk_model.features import FEATURE_NAMES

    # Create dummy DataFrame with contaminated SUP-1047 rows
    contaminated_data = {f: [0.5, 0.6] for f in FEATURE_NAMES}
    contaminated_data["supplier_id"] = ["SUP-1047", "SUP-1047"]
    contaminated_data["date"] = ["2026-07-15", "2026-08-01"]
    contaminated_data["disrupted"] = [1, 1]
    contaminated_df = pd.DataFrame(contaminated_data)

    model = SupplierRiskModel(model_type="logistic")
    with pytest.raises(ValueError, match="Contamination detected"):
        model.fit(contaminated_df)
