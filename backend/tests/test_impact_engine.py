"""Tests for Sprint 4: Deterministic Impact Engine and Multi-Level Supply Network Traversal."""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.impact import DirectImpactInputs
from app.services.impact_engine import (
    ImpactInputs,
    calculate_buffer_runway,
    calculate_direct_whatif,
    calculate_impact,
    calculate_inventory_runway,
    calculate_priority_index,
    calculate_revenue_exposure,
    calculate_units_at_risk,
    traverse_supplier_network,
)
from scripts.generate_synthetic_data import generate

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "generated"

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def ensure_dataset():
    """Ensure small scale synthetic dataset exists."""
    if not (DATA_DIR / "supplier.csv").exists():
        generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")


def test_impact_calculation_reconciles():
    """Legacy formula test must preserve backward compatibility."""
    inputs = ImpactInputs(
        on_hand_units=90,
        average_daily_consumption=30,
        units_at_risk=100,
        contribution_margin_per_unit_inr=250,
        stockout_probability=0.4,
    )
    output = calculate_impact(inputs)
    assert output["inventory_runway_days"] == 3.0
    assert output["revenue_exposure_inr"] == 10_000.0
    assert "formula_version" in output
    assert "assumption" in output


def test_negative_units_are_rejected():
    """Negative units or invalid probability bounds must raise ValueError."""
    with pytest.raises(ValueError):
        calculate_impact(ImpactInputs(-1, 1, 1, 1, 0.5))

    with pytest.raises(ValueError):
        calculate_inventory_runway(-10.0, 5.0)

    with pytest.raises(ValueError):
        calculate_inventory_runway(10.0, -5.0)

    with pytest.raises(ValueError):
        calculate_revenue_exposure(100, 200, 1.5)


def test_deterministic_runway_and_buffer_penetration():
    """Runway and safety stock buffer calculations must be exact and divide-by-zero safe."""
    # Standard cover
    runway = calculate_inventory_runway(300.0, 50.0)
    assert runway == 6.0

    # Buffer runway (days until safety stock breached)
    buffer_days = calculate_buffer_runway(
        on_hand_units=300.0,
        safety_stock_units=100.0,
        average_daily_consumption=50.0,
    )
    assert buffer_days == 4.0

    # Safety stock already breached
    buffer_breached = calculate_buffer_runway(
        on_hand_units=80.0,
        safety_stock_units=100.0,
        average_daily_consumption=50.0,
    )
    assert buffer_breached == 0.0

    # Zero consumption guard
    zero_burn_runway = calculate_inventory_runway(200.0, 0.0)
    assert zero_burn_runway == 999.0


def test_units_at_risk_and_revenue_exposure_formula():
    """Exposure must strictly reconcile to units at risk * contribution margin * P(stockout)."""
    # 50 daily burn * 14 days disruption = 700 demanded
    # On-hand 200 + Open PO 100 = 300 available
    # Shortage / units at risk = 400
    units_risk = calculate_units_at_risk(
        average_daily_consumption=50.0,
        disruption_lead_time_days=14.0,
        on_hand_units=200.0,
        open_po_units=100.0,
    )
    assert units_risk == 400.0

    # Sufficient inventory: no units at risk
    no_shortage = calculate_units_at_risk(
        average_daily_consumption=10.0,
        disruption_lead_time_days=14.0,
        on_hand_units=200.0,
        open_po_units=100.0,
    )
    assert no_shortage == 0.0

    # Revenue exposure in INR
    margin = 2500.0
    p_stockout = 0.75
    exposure = calculate_revenue_exposure(units_risk, margin, p_stockout)
    expected_exposure = 400.0 * 2500.0 * 0.75  # 750,000 INR
    assert exposure == expected_exposure


def test_priority_index_bounds_and_ranking():
    """Composite priority index must be within [0, 100] and monotonically penalize shorter runways."""
    high_urgency = calculate_priority_index(risk_score=86.0, revenue_exposure_inr=30_000_000.0, min_runway_days=2.5)
    low_urgency = calculate_priority_index(risk_score=86.0, revenue_exposure_inr=30_000_000.0, min_runway_days=25.0)

    assert 0.0 <= high_urgency <= 100.0
    assert 0.0 <= low_urgency <= 100.0
    assert high_urgency > low_urgency


def test_multi_level_network_traversal_sup_1047():
    """Traverse supply network for flagship ApexDrive Components (SUP-1047)."""
    report = traverse_supplier_network(
        supplier_id="SUP-1047",
        data_dir=DATA_DIR,
        disruption_lead_time_days=14.0,
        stockout_probability=0.85,
        as_of_date="2026-09-30",
    )

    assert report.supplier_id == "SUP-1047"
    assert "ApexDrive" in report.supplier_name
    assert report.disruption_lead_time_days == 14.0
    assert report.stockout_probability_used == 0.85
    assert report.total_revenue_exposure_inr > 0.0
    assert report.min_inventory_runway_days >= 0.0
    assert report.affected_sku_count > 0

    # Assert affected plants include NovaHome manufacturing plants (Pune, Chennai, Greater Noida)
    valid_plants = {"Pune", "Chennai", "Greater Noida", "GreaterNoida"}
    assert set(report.affected_plants).issubset(valid_plants)

    # Inspect Plant Vulnerability Breakdown
    assert len(report.plant_impacts) > 0
    for plant_imp in report.plant_impacts:
        assert plant_imp.plant in valid_plants
        assert plant_imp.affected_sku_count > 0
        assert plant_imp.total_revenue_exposure_inr >= 0.0
        assert plant_imp.downtime_risk_level in {"CRITICAL", "ELEVATED", "MODERATE", "CONTROLLED"}

    # Inspect Graph Nodes and Edges
    graph = report.dependency_graph
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0

    node_types = {n.node_type for n in graph.nodes}
    assert {"SUPPLIER", "CATEGORY", "SKU", "PLANT"}.issubset(node_types)

    # Lineage verification
    assert "supplier_source" in report.lineage
    assert "sku_source" in report.lineage
    assert "inventory_source" in report.lineage
    assert "po_source" in report.lineage


def test_network_traversal_nonexistent_supplier_raises_404():
    """Non-existent supplier ID must raise ValueError."""
    with pytest.raises(ValueError):
        traverse_supplier_network(supplier_id="SUP-NONEXISTENT", data_dir=DATA_DIR)


def test_impact_api_endpoints():
    """Verify POST /api/v1/impact/calculate and GET endpoints."""
    # 1. Direct what-if calculation
    res_direct = client.post(
        "/api/v1/impact/calculate",
        json={
            "custom_inputs": {
                "on_hand_units": 150.0,
                "average_daily_consumption": 25.0,
                "safety_stock_units": 50.0,
                "units_at_risk": 80.0,
                "contribution_margin_per_unit_inr": 1200.0,
                "stockout_probability": 0.5,
            }
        },
    )
    assert res_direct.status_code == 200
    direct_data = res_direct.json()
    assert direct_data["mode"] == "direct_simulation"
    assert direct_data["result"]["inventory_runway_days"] == 6.0
    assert direct_data["result"]["buffer_penetration_days"] == 4.0
    assert direct_data["result"]["revenue_exposure_inr"] == 48_000.0

    # 2. Network traversal calculation
    res_network = client.post(
        "/api/v1/impact/calculate",
        json={
            "supplier_id": "SUP-1047",
            "disruption_lead_time_days": 14.0,
            "as_of_date": "2026-09-30",
        },
    )
    assert res_network.status_code == 200
    net_data = res_network.json()
    assert net_data["mode"] == "network_traversal"
    assert net_data["report"]["supplier_id"] == "SUP-1047"
    assert net_data["report"]["total_revenue_exposure_inr"] > 0

    # 3. GET /api/v1/impact/supplier/SUP-1047
    res_get_sup = client.get("/api/v1/impact/supplier/SUP-1047?disruption_days=10")
    assert res_get_sup.status_code == 200
    report_data = res_get_sup.json()
    assert report_data["supplier_id"] == "SUP-1047"
    assert len(report_data["plant_impacts"]) > 0

    # 4. GET /api/v1/impact/network/SUP-1047
    res_graph = client.get("/api/v1/impact/network/SUP-1047")
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data

    # 5. Invalid supplier 404 handling
    res_bad = client.get("/api/v1/impact/supplier/SUP-999999")
    assert res_bad.status_code == 404
