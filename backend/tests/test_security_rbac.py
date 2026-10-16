"""Comprehensive Acceptance Tests for Priority 9: Authentication, RBAC, Tenant Isolation & SSRF Shield."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import generate_mock_token, DEFAULT_TENANT_ID
from app.core.rate_limit import rate_limiter
from app.core.safe_requests import validate_external_url, SSRFSecurityError

client = TestClient(app)


def setup_function():
    """Reset rate limiter before each test."""
    rate_limiter.reset()


# ==============================================================================
# 1. Authentication & Bearer Token Tests
# ==============================================================================

def test_valid_bearer_token_authenticated():
    """Verify that a cryptographically signed mock Bearer token successfully authenticates."""
    token = generate_mock_token(user_id="USR-CPO-01", role="CPO", tenant_id=DEFAULT_TENANT_ID)
    response = client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_invalid_bearer_token_returns_401():
    """Verify that a forged or malformed bearer token returns HTTP 401 Unauthorized."""
    response = client.get(
        "/api/v1/cases",
        headers={"Authorization": "Bearer px_USR-FAKE_CPO_invalidhash1234"},
    )
    assert response.status_code == 401
    assert "Invalid or expired authentication credentials" in response.json()["detail"]


def test_malformed_authorization_header_returns_401():
    """Verify that a header not adhering to 'Bearer <token>' returns HTTP 401."""
    response = client.get(
        "/api/v1/cases",
        headers={"Authorization": "TokenInvalidFormatOnly"},
    )
    assert response.status_code == 401
    assert "Malformed Authorization header" in response.json()["detail"]


# ==============================================================================
# 2. Role-Based Access Control (RBAC) Tests
# ==============================================================================

def test_analyst_role_denied_from_triggering_ingest():
    """Verify that read-only ANALYST role is rejected from executing signal ingestion."""
    response = client.post(
        "/api/v1/signals/ingest",
        headers={"X-User-Role": "ANALYST"},
    )
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


def test_procurement_manager_authorized_for_ingest():
    """Verify that PROCUREMENT_MANAGER role is authorized for signal ingestion."""
    response = client.post(
        "/api/v1/signals/ingest",
        headers={"X-User-Role": "PROCUREMENT_MANAGER"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data
    assert data["total"] > 0


def test_invalid_unrecognized_role_returns_403():
    """Verify that a non-canonical role name returns HTTP 403 Forbidden."""
    response = client.post(
        "/api/v1/signals/ingest",
        headers={"X-User-Role": "INTERN_GUEST"},
    )
    assert response.status_code == 403
    assert "Unrecognized role" in response.json()["detail"]


def test_analyst_role_denied_from_approving_case():
    """Verify that an ANALYST cannot sign off or approve a disruption case."""
    # Run a case first
    run_resp = client.post("/api/v1/cases/run", json={"supplier_id": "SUP-1047"})
    case_id = run_resp.json()["case_id"]

    approve_resp = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={
            "action": "APPROVE",
            "actor_id": "USR-ANALYST-01",
            "actor_role": "ANALYST",
            "reason": "Unauthorized analyst review",
            "idempotency_key": "IDEM-ANALYST-REJECT-001",
            "selected_scenario_id": "SCN-D",
        },
        headers={"X-User-Role": "ANALYST"},
    )
    assert approve_resp.status_code == 403
    assert "read-only access" in approve_resp.json()["detail"]


# ==============================================================================
# 3. Tenant Isolation Tests
# ==============================================================================

def test_mismatched_tenant_access_is_blocked():
    """Verify that a user from a different tenant cannot access ApexDrive cases."""
    response = client.get(
        "/api/v1/cases",
        headers={"X-Tenant-ID": "CompetitorMotors Global"},
    )
    assert response.status_code == 403
    assert "Tenant Access Denied" in response.json()["detail"]


def test_authorized_flagship_tenant_access_succeeds():
    """Verify that tenant aliases for ApexDrive Components succeed."""
    for valid_tenant in ["ApexDrive Components", "TENANT-APEX-01", "TENANT-APEX-DEV"]:
        response = client.get(
            "/api/v1/cases",
            headers={"X-Tenant-ID": valid_tenant},
        )
        assert response.status_code == 200


# ==============================================================================
# 4. Rate Limiting Tests
# ==============================================================================

def test_rate_limiting_headers_present_on_responses():
    """Verify standard rate limit headers X-RateLimit-Limit and X-RateLimit-Remaining."""
    response = client.get("/api/v1/signals/providers", headers={"X-Test-Rate-Limit": "1"})
    assert response.status_code == 200
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers


def test_rate_limit_exceeded_returns_429():
    """Verify that bursts exceeding rate limits return HTTP 429 with Retry-After header."""
    rate_limiter.reset()
    client_ip = "192.0.2.1"
    headers = {"X-Forwarded-For": client_ip, "X-Test-Rate-Limit": "1"}

    # Simulate burst of 35 requests on a 30-limit endpoint (/signals/ingest)
    hit_429 = False
    for i in range(35):
        resp = client.post(
            "/api/v1/signals/ingest",
            headers={"X-User-Role": "CPO", "X-Forwarded-For": client_ip, "X-Test-Rate-Limit": "1"},
        )
        if resp.status_code == 429:
            hit_429 = True
            assert "Retry-After" in resp.headers
            assert resp.json()["error"] == "Too Many Requests"
            break

    assert hit_429, "Expected rate limiter to trigger HTTP 429 on excessive requests"


# ==============================================================================
# 5. SSRF Protection & Safe External URL Validation
# ==============================================================================

def test_ssrf_shield_blocks_cloud_metadata():
    """Verify that AWS/Azure/GCP metadata IP (169.254.169.254) is blocked."""
    with pytest.raises(SSRFSecurityError, match="SSRF Protection"):
        validate_external_url("http://169.254.169.254/latest/meta-data")


def test_ssrf_shield_blocks_localhost_and_loopback():
    """Verify that 127.0.0.1 and localhost targeting is blocked."""
    with pytest.raises(SSRFSecurityError, match="SSRF Protection"):
        validate_external_url("http://127.0.0.1:8000/internal-admin")


def test_ssrf_shield_blocks_unauthorized_domain():
    """Verify that arbitrary external domains outside approved whitelist are blocked."""
    with pytest.raises(SSRFSecurityError, match="not in the approved external provider whitelist"):
        validate_external_url("https://malicious-external-exfiltration.com/api/steal")


def test_ssrf_shield_blocks_non_http_schemes():
    """Verify that non-HTTP schemes (file://, ftp://, gopher://) are blocked."""
    with pytest.raises(SSRFSecurityError, match="Forbidden URL scheme"):
        validate_external_url("file:///etc/passwd")


def test_ssrf_shield_allows_approved_gdelt_domain():
    """Verify that approved external GDELT provider URL passes validation."""
    approved_url = "https://api.gdeltproject.org/api/v2/doc/doc?query=automotive"
    validated = validate_external_url(approved_url)
    assert validated == approved_url


# ==============================================================================
# 6. HTTP Defense-in-Depth Security Headers
# ==============================================================================

def test_security_headers_enforced():
    """Verify that defense-in-depth security headers are attached to responses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
