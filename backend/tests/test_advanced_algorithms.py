"""Tests for advanced predictive algorithms, time-series forecasting, NLP sentiment velocity, and Pareto optimization.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.forecasting.demand_forecast import HoltWintersForecaster
from app.services.signal_intelligence.sentiment_analyzer import (
    DomainSentimentAnalyzer,
    DisruptionVelocityCalculator,
)
from app.services.optimizer.pareto_solver import (
    ParetoMultiObjectiveOptimizer,
    StatisticalSafetyStockOptimizer,
)
from app.services.risk_model.model import SupplierRiskModel
import pandas as pd
import numpy as np


@pytest.fixture
def client():
    return TestClient(app)


def test_holt_winters_forecasting():
    """Verify Holt-Winters additive exponential smoothing with 95% confidence intervals."""
    # 21 days historical demand with 7-day seasonality
    base_demand = [200, 210, 225, 230, 240, 190, 180] * 3
    forecaster = HoltWintersForecaster(alpha=0.3, beta=0.1, gamma=0.2, season_length=7)

    result = forecaster.fit_predict(base_demand, horizon=14, target_name="Pune EV Battery Demand")

    assert result.algorithm == "Holt-Winters Triple Exponential Smoothing"
    assert len(result.forecast_points) == 14
    assert result.seasonality_period == 7
    assert result.mae >= 0.0
    assert result.rmse >= 0.0
    assert result.mape_pct >= 0.0

    # Ensure 95% confidence bounds wrap the forecast
    for pt in result.forecast_points:
        assert pt.predicted_value >= 0.0
        assert pt.lower_bound_95 <= pt.predicted_value <= pt.upper_bound_95


def test_domain_sentiment_analyzer():
    """Verify supply-chain domain lexicon scoring."""
    analyzer = DomainSentimentAnalyzer()

    # Severe disruption statement
    severe_res = analyzer.analyze_text(
        "Mundra port faces acute demurrage congestion and dockworker strike causing supplier delivery delay."
    )
    assert severe_res.compound_score < -0.30
    assert severe_res.classification == "HIGH_RISK"
    assert "strike" in severe_res.detected_keywords
    assert "demurrage" in severe_res.detected_keywords

    # Resilience statement
    positive_res = analyzer.analyze_text(
        "Dispute is settled and container shipments are cleared, with surplus dual-sourcing approved."
    )
    assert positive_res.compound_score > 0.20
    assert positive_res.classification == "POSITIVE_RESILIENCE"
    assert "settled" in positive_res.detected_keywords


def test_disruption_velocity_and_volatility():
    """Verify temporal rate-of-change and governed market stress index."""
    # Rapid sentiment collapse across 4 periods
    sentiment_series = [0.25, 0.10, -0.15, -0.55]
    metrics = DisruptionVelocityCalculator.calculate_velocity(
        entity_name="SUP-1047",
        sentiment_history=sentiment_series,
        time_delta_days=1.0,  # Daily tracking frequency
    )

    assert metrics.entity_name == "SUP-1047"
    assert metrics.current_sentiment == -0.55
    assert metrics.velocity_per_day < -0.10  # Rapidly dropping
    assert metrics.volatility_14d > 0.0
    assert metrics.market_stress_index >= 60.0  # Elevated/Critical stress
    assert metrics.early_warning_tier in ["ELEVATED", "CRITICAL"]


def test_pareto_multi_objective_optimizer():
    """Verify Pareto frontier solver generates non-dominated trade-offs."""
    result = ParetoMultiObjectiveOptimizer.solve_frontier(
        shortage_units=1500,
        primary_delay_days=14.0,
        unit_downtime_penalty_inr=3800.0,
        secondary_unit_cost_inr=950.0,
        expedite_premium_inr=380.0,
        secondary_capacity_limit=1200,
    )

    assert len(result.frontier_solutions) >= 3
    assert result.dominated_solutions_count >= 1
    assert result.knee_point_id == "PAR-OPT-BALANCED"

    # Verify solutions are sorted and possess positive service level
    for sol in result.frontier_solutions:
        assert sol.is_pareto_optimal is True
        assert 0.0 < sol.service_level_pct <= 100.0
        assert sol.mitigation_cost_inr > 0.0
        assert sol.lead_time_recovery_days > 0.0


def test_statistical_safety_stock():
    """Verify safety stock convolution formula under lead time and demand uncertainty."""
    res = StatisticalSafetyStockOptimizer.calculate_safety_stock(
        plant_node="Pune Central Assembly",
        avg_daily_demand=250.0,
        demand_std=30.0,
        lead_time_days=10.0,
        lead_time_std=2.0,
        target_service_level_pct=97.5,
    )

    assert res.plant_node == "Pune Central Assembly"
    assert res.z_score == 1.96
    assert res.recommended_safety_stock_units > 0
    assert res.reorder_point_units > res.recommended_safety_stock_units
    assert res.runway_days_supported > 0.0


def test_gradient_boosting_and_ensemble_models():
    """Verify SupplierRiskModel supports gradient_boosting and soft-voting ensemble."""
    # Synthetic small dataset
    from app.services.risk_model.features import FEATURE_NAMES

    np.random.seed(42)
    n = 80
    data = {feat: np.random.rand(n) for feat in FEATURE_NAMES}
    data["disrupted"] = np.random.choice([0, 1], size=n, p=[0.75, 0.25])
    df = pd.DataFrame(data)

    for m_type in ["gradient_boosting", "ensemble"]:
        model = SupplierRiskModel(model_type=m_type)
        model.fit(df)
        assert model.is_fitted is True

        proba = model.predict_proba(df)
        assert len(proba) == n
        assert all(0.0 <= p <= 1.0 for p in proba)

        single_p = model.predict_single({feat: 0.5 for feat in FEATURE_NAMES})
        assert 0.0 <= single_p <= 1.0


def test_analytics_api_endpoints(client):
    """Verify REST endpoints for algorithms, benchmarks, forecasting, sentiment, and Pareto solver."""
    # 1. Algorithms Registry
    resp = client.get("/api/v1/analytics/algorithms")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert data["total_algorithms_active"] == 7

    # 2. Benchmarks
    resp = client.get("/api/v1/analytics/models/benchmark")
    assert resp.status_code == 200
    bench = resp.json()
    assert bench["champion_model"] == "ensemble"
    assert len(bench["models"]) == 4

    # 3. Demand Forecast
    resp = client.post(
        "/api/v1/analytics/forecast/demand",
        json={
            "series": [150, 160, 175, 170, 180, 140, 130] * 3,
            "horizon_days": 10,
            "target_metric_name": "Battery Pack Demand",
        },
    )
    assert resp.status_code == 200
    fc = resp.json()
    assert len(fc["forecast_series"]) == 10
    assert "mae" in fc["accuracy_metrics"]

    # 4. Sentiment Score
    resp = client.post(
        "/api/v1/analytics/sentiment/score",
        json={
            "text": "Port of Mundra demurrage strikes delay shipments across northern corridor.",
            "entity_name": "CORRIDOR-MUNDRA-PUNE",
            "sentiment_history": [0.2, 0.05, -0.45],
        },
    )
    assert resp.status_code == 200
    sent = resp.json()
    assert sent["compound_score"] < 0
    assert sent["velocity_metrics"]["market_stress_index"] > 40

    # 5. Pareto Optimization
    resp = client.post(
        "/api/v1/analytics/optimizer/pareto",
        json={
            "shortage_units": 1200,
            "primary_delay_days": 12.0,
            "unit_downtime_penalty_inr": 3500.0,
            "secondary_unit_cost_inr": 890.0,
            "expedite_premium_inr": 350.0,
            "secondary_capacity_limit": 1000,
        },
    )
    assert resp.status_code == 200
    pareto = resp.json()
    assert len(pareto["frontier_solutions"]) >= 3
    assert pareto["knee_point_id"] == "PAR-OPT-BALANCED"

    # 6. Safety Stock
    resp = client.post(
        "/api/v1/analytics/safety-stock",
        json={
            "plant_node": "Sanand Hub",
            "avg_daily_demand": 180.0,
            "demand_std_dev": 22.0,
            "lead_time_days": 8.0,
            "lead_time_std_dev": 1.5,
            "target_service_level_pct": 97.5,
        },
    )
    assert resp.status_code == 200
    ss = resp.json()
    assert ss["recommendations"]["safety_stock_units"] > 0
    assert ss["recommendations"]["reorder_point_units"] > 0
