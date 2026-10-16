"""Tests for Priority 4: Signal freshness, safe retries, error recovery, and persistence repository."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.signal_intelligence.base_provider import BaseSignalProvider, utc_now_iso
from app.services.signal_intelligence.freshness import calculate_signal_freshness
from app.services.signal_intelligence.repository import SignalRepository
from app.services.signal_intelligence.schema import (
    NormalizedSignal,
    ProviderFetchResult,
    ProviderHealth,
    ProviderStatus,
)
from app.services.signal_intelligence.service import SignalIntelligenceService

client = TestClient(app)


def test_freshness_calculation_tiers():
    """Verify freshness classification into fresh, recent, stale, archived."""
    now = datetime.now(timezone.utc)

    # 1. 2 hours old -> 'fresh' (< 24h)
    two_hours_ago = (now - timedelta(hours=2)).isoformat()
    status, age = calculate_signal_freshness(two_hours_ago)
    assert status == "fresh"
    assert age is not None
    assert 1.5 <= age <= 2.5

    # 2. 36 hours old -> 'recent' (24h to 72h)
    day_and_half_ago = (now - timedelta(hours=36)).isoformat()
    status, age = calculate_signal_freshness(day_and_half_ago)
    assert status == "recent"
    assert 35.0 <= age <= 37.0

    # 3. 4 days old -> 'stale' (72h to 168h)
    four_days_ago = (now - timedelta(days=4)).isoformat()
    status, age = calculate_signal_freshness(four_days_ago)
    assert status == "stale"
    assert 95.0 <= age <= 97.0

    # 4. 10 days old -> 'archived' (>= 168h)
    ten_days_ago = (now - timedelta(days=10)).isoformat()
    status, age = calculate_signal_freshness(ten_days_ago)
    assert status == "archived"
    assert age >= 239.0

    # 5. Invalid string -> 'unknown'
    status, age = calculate_signal_freshness("invalid-timestamp")
    assert status == "unknown"
    assert age is None


class FlakyNetworkProvider(BaseSignalProvider):
    provider_name = "MockFlaky"

    def __init__(self, fail_count: int = 1):
        self.call_count = 0
        self.fail_count = fail_count

    def is_configured(self) -> bool:
        return True

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(provider=self.provider_name, configured=True, status=ProviderStatus.SUCCESS, message="OK")

    def fetch_live(self, query: str | None = None, limit: int = 25) -> ProviderFetchResult:
        self.call_count += 1
        if self.call_count <= self.fail_count:
            raise httpx.ConnectError("Simulated connection timeout")
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=1,
            normalized_signals=[
                NormalizedSignal(
                    signal_id="SIG-RETRY-OK",
                    provider=self.provider_name,
                    canonical_url="https://example.com/retry-ok",
                    title="Recovery Signal",
                    description_or_snippet="Recovered after transient drop",
                    publisher="Reuters",
                    published_at_utc=utc_now_iso(),
                    retrieved_at_utc=utc_now_iso(),
                    language="en",
                    content_hash="hash-retry-1",
                )
            ],
        )

    def fetch_fixture(self) -> ProviderFetchResult:
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=0,
            normalized_signals=[],
            is_mock=True,
        )


def test_safe_retry_recovers_from_transient_error():
    """Provider must retry on transient network errors and succeed within retry budget."""
    provider = FlakyNetworkProvider(fail_count=1)
    res = provider.fetch(use_live=True)
    assert res.status == ProviderStatus.SUCCESS
    assert provider.call_count == 2
    assert len(res.normalized_signals) == 1
    assert res.normalized_signals[0].freshness_status == "fresh"


def test_safe_retry_exhaustion_returns_clean_timeout():
    """Provider failing continuously must exhaust retries without unhandled crash and return TIMEOUT status."""
    provider = FlakyNetworkProvider(fail_count=5)
    res = provider.fetch(use_live=True)
    assert res.status == ProviderStatus.TIMEOUT
    assert res.result_count == 0
    assert "network failed after" in (res.error_message or "").lower()


def test_signal_repository_graceful_offline_behavior():
    """SignalRepository must handle unconfigured or unreachable database gracefully."""
    repo = SignalRepository(db_url="")
    assert not repo.is_available()

    sig = NormalizedSignal(
        signal_id="SIG-TEST-OFFLINE",
        provider="GDELT",
        canonical_url="https://example.com/test",
        title="Test Signal",
        description_or_snippet="Snippet",
        publisher="GDELT",
        published_at_utc=utc_now_iso(),
        retrieved_at_utc=utc_now_iso(),
        language="en",
        content_hash="test-hash-offline",
    )
    count = repo.persist_signals([sig])
    assert count == 0
    persisted_list = repo.fetch_persisted_signals()
    assert persisted_list == []


def test_signals_api_includes_freshness_and_persisted_contract():
    """GET /api/v1/signals must return freshness_status, age_hours, and persisted fields."""
    res = client.get("/api/v1/signals")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    first = data["signals"][0]

    assert "freshness_status" in first
    assert first["freshness_status"] in {"fresh", "recent", "stale", "archived", "unknown"}
    assert "persisted" in first
    assert isinstance(first["persisted"], bool)
    assert "content_hash" in first
