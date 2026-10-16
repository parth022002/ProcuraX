from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_reports_scaffold_status():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["implementation_status"] == "scaffold"


def test_business_endpoint_does_not_claim_success_when_unimplemented():
    response = client.post("/api/v1/evaluation/run")
    assert response.status_code == 501


def test_supplier_360_endpoint_returns_data_for_known_supplier():
    response = client.get("/api/v1/suppliers/SUP-1047/360")
    assert response.status_code == 200
    data = response.json()
    assert "supplier" in data
    assert data["supplier"]["supplier_id"] == "SUP-1047"
    assert "po_summary" in data
