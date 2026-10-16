"""Tests for Sprint 3: Signal Intelligence, Provider Adapters, Entity Resolution, and API Routes."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.signal_intelligence.base_provider import utc_now_iso
from app.services.signal_intelligence.deduplication import canonicalize_url, compute_content_hash, deduplicate_signals
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.providers.alpha_vantage import AlphaVantageProvider
from app.services.signal_intelligence.providers.gdelt import GdeltProvider
from app.services.signal_intelligence.providers.marketaux import MarketauxProvider
from app.services.signal_intelligence.providers.newsdata import NewsDataProvider
from app.services.signal_intelligence.providers.sec_edgar import SecEdgarProvider
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderStatus
from app.services.signal_intelligence.service import signal_service

client = TestClient(app)


def test_provider_health_check_no_secret_leakage():
    """Providers must report status accurately and never leak raw API keys."""
    health_list = signal_service.check_provider_health()
    assert len(health_list) == 5

    provider_names = {h.provider for h in health_list}
    assert provider_names == {"GDELT", "Marketaux", "Alpha Vantage", "NewsData.io", "SEC EDGAR"}

    for h in health_list:
        # Assert secrets are not leaked in message and standard safe statuses are reported
        assert (
            "key" not in h.message.lower()
            or "not set" in h.message.lower()
            or "configured" in h.message.lower()
            or "public" in h.message.lower()
        )
        assert not hasattr(h, "api_key")
        assert not hasattr(h, "token")


def test_unconfigured_provider_graceful_handling():
    """Unconfigured provider must return NOT_CONFIGURED status without crashing or throwing unhandled exceptions."""
    mkt = MarketauxProvider()
    # Ensure token is empty
    orig = settings.marketaux_api_token
    try:
        settings.marketaux_api_token = ""
        assert not mkt.is_configured()
        res = mkt.fetch(use_live=True)
        assert res.status == ProviderStatus.NOT_CONFIGURED
        assert res.result_count == 0
        assert "not configured" in (res.error_message or "").lower()
    finally:
        settings.marketaux_api_token = orig


def test_fixture_normalization_and_provenance():
    """All 5 providers must normalize fixture payloads to canonical schema with PUBLIC_REAL provenance."""
    providers = [
        GdeltProvider(),
        MarketauxProvider(),
        AlphaVantageProvider(),
        NewsDataProvider(),
        SecEdgarProvider(),
    ]

    for p in providers:
        res = p.fetch_fixture()
        assert res.status == ProviderStatus.SUCCESS
        assert res.result_count > 0
        for sig in res.normalized_signals:
            assert sig.provider == p.provider_name
            assert sig.title
            assert sig.canonical_url.startswith("http")
            assert sig.provenance == "PUBLIC_REAL"
            assert sig.content_hash
            assert sig.retrieved_at_utc


def test_deduplication_and_corroboration():
    """Deduplication must collapse identical articles and increment corroboration counts."""
    sig1 = NormalizedSignal(
        signal_id="SIG-TEST-1",
        provider="GDELT",
        canonical_url="https://www.reuters.com/markets/copper-news-2026?utm_source=rss",
        title="Copper Supply Constraint Hits Refineries",
        description_or_snippet="News snippet",
        publisher="Reuters",
        published_at_utc=utc_now_iso(),
        retrieved_at_utc=utc_now_iso(),
        language="en",
        content_hash="",
    )
    # Duplicate with different URL query params
    sig2 = NormalizedSignal(
        signal_id="SIG-TEST-2",
        provider="Marketaux",
        canonical_url="https://reuters.com/markets/copper-news-2026",
        title="Copper Supply Constraint Hits Refineries",
        description_or_snippet="Duplicate snippet",
        publisher="Reuters",
        published_at_utc=utc_now_iso(),
        retrieved_at_utc=utc_now_iso(),
        language="en",
        content_hash="",
    )

    deduped = deduplicate_signals([sig1, sig2])
    assert len(deduped) == 1, "Duplicate canonical articles must collapse into single record"
    assert deduped[0].raw_metadata.get("corroboration_count", 1) >= 2


def test_entity_resolution_and_scenario_disclaimer():
    """Signals matching flagship keywords (ApexDrive, copper, BLDC motor) must map to SUP-1047 with disclaimer."""
    raw_sig = NormalizedSignal(
        signal_id="SIG-RAW-1",
        provider="GDELT",
        canonical_url="https://example.com/article",
        title="ApexDrive Components Faces Severe Copper Wire Backlogs",
        description_or_snippet="BLDC motor manufacturing slowed due to raw material shortage in Maharashtra.",
        publisher="Industry News",
        published_at_utc=utc_now_iso(),
        retrieved_at_utc=utc_now_iso(),
        language="en",
        content_hash="hash-1",
    )

    resolved = resolve_signal_entity(raw_sig)
    assert resolved.mapped_supplier_id == "SUP-1047"
    assert resolved.mapping_confidence >= 0.70
    assert resolved.scenario_disclaimer is not None
    assert "Scenario assumption" in resolved.scenario_disclaimer
    assert resolved.event_type == "raw_material_shortage"
    assert resolved.event_severity >= 0.60


def test_signals_api_endpoints():
    """Test GET /api/v1/signals, GET /api/v1/signals/providers, and POST /api/v1/signals/ingest."""
    # 1. Provider health endpoint
    res_providers = client.get("/api/v1/signals/providers")
    assert res_providers.status_code == 200
    providers = res_providers.json()
    assert len(providers) == 5
    for p in providers:
        assert "provider" in p
        assert "status" in p
        assert "configured" in p

    # 2. Signals list endpoint
    res_signals = client.get("/api/v1/signals")
    assert res_signals.status_code == 200
    data = res_signals.json()
    assert "signals" in data
    assert "scenario_banner" in data
    assert data["total"] > 0

    first = data["signals"][0]
    assert "signal_id" in first
    assert "provenance" in first
    assert first["provenance"] == "PUBLIC_REAL"

    # 3. Filter by mapped flagship supplier SUP-1047
    res_sup = client.get("/api/v1/signals?supplier_id=SUP-1047")
    assert res_sup.status_code == 200
    sup_data = res_sup.json()
    assert sup_data["total"] > 0
    for s in sup_data["signals"]:
        assert s["mapped_supplier_id"] == "SUP-1047"
        assert s["scenario_disclaimer"] is not None

    # 4. Filter by provider GDELT
    res_gdelt = client.get("/api/v1/signals?provider=GDELT")
    assert res_gdelt.status_code == 200
    gdelt_data = res_gdelt.json()
    for s in gdelt_data["signals"]:
        assert s["provider"] == "GDELT"

    # 5. Trigger ingest endpoint
    res_ingest = client.post("/api/v1/signals/ingest")
    assert res_ingest.status_code == 200
    ingest_data = res_ingest.json()
    assert ingest_data["total"] > 0
