"""Abstract base provider protocol for external signal adapters with safe retries."""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.services.signal_intelligence.freshness import calculate_signal_freshness
from app.services.signal_intelligence.schema import (
    NormalizedSignal,
    ProviderFetchResult,
    ProviderHealth,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseSignalProvider(ABC):
    """Abstract signal intelligence provider adapter with safe retries and freshness calculation."""

    provider_name: str
    last_fetched_at: str | None = None

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if credentials and network configuration are present."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Check status of API key configuration and reachability without exposing secrets."""
        pass

    @abstractmethod
    def fetch_live(self, query: str | None = None, limit: int = 25) -> ProviderFetchResult:
        """Perform live network fetch to external provider."""
        pass

    @abstractmethod
    def fetch_fixture(self) -> ProviderFetchResult:
        """Return deterministic offline fixture results for CI and offline replays."""
        pass

    def _apply_freshness(self, signals: list[NormalizedSignal]) -> list[NormalizedSignal]:
        """Compute and set freshness status and age in hours for all signals."""
        for sig in signals:
            status, age = calculate_signal_freshness(sig.published_at_utc or sig.retrieved_at_utc)
            sig.freshness_status = status
            sig.age_hours = age
        return signals

    def fetch(self, query: str | None = None, limit: int = 25, use_live: bool = False) -> ProviderFetchResult:
        """Fetch signals using live API if enabled and configured, otherwise return fixture."""
        if use_live:
            if not self.is_configured():
                return ProviderFetchResult(
                    provider=self.provider_name,
                    status=ProviderStatus.NOT_CONFIGURED,
                    fetched_at_utc=utc_now_iso(),
                    result_count=0,
                    normalized_signals=[],
                    error_message=f"{self.provider_name} API credentials not configured in environment.",
                )

            # Retry wrapper with exponential backoff (2 attempts maximum)
            attempts = 0
            max_retries = 2
            last_error: Exception | None = None

            while attempts <= max_retries:
                attempts += 1
                try:
                    res = self.fetch_live(query=query, limit=limit)
                    self.last_fetched_at = res.fetched_at_utc
                    res.normalized_signals = self._apply_freshness(res.normalized_signals)
                    return res
                except (httpx.ConnectError, httpx.TimeoutException, httpx.ConnectTimeout) as net_err:
                    last_error = net_err
                    if attempts <= max_retries:
                        backoff = 0.5 * (2 ** (attempts - 1))
                        logger.warning(
                            "Transient network error on %s (attempt %d/%d). Backing off %.1fs: %s",
                            self.provider_name,
                            attempts,
                            max_retries + 1,
                            backoff,
                            net_err,
                        )
                        time.sleep(backoff)
                        continue
                except Exception as exc:
                    logger.error("Non-retryable error in %s: %s", self.provider_name, exc)
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.ERROR,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message=f"Live fetch failed: {str(exc)}",
                    )

            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.TIMEOUT,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message=f"Network failed after {max_retries + 1} attempts: {str(last_error)}",
            )

        fixture_res = self.fetch_fixture()
        self.last_fetched_at = fixture_res.fetched_at_utc
        fixture_res.normalized_signals = self._apply_freshness(fixture_res.normalized_signals)
        return fixture_res
