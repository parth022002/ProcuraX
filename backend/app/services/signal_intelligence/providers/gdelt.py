"""GDELT Project DOC API v2 adapter."""
from __future__ import annotations

import httpx

from app.services.signal_intelligence.base_provider import BaseSignalProvider, utc_now_iso
from app.services.signal_intelligence.deduplication import compute_content_hash
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.fixtures import FIXTURE_GDELT
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderFetchResult, ProviderHealth, ProviderStatus

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_QUERY = '"supply chain" OR "raw material shortage" OR "port disruption" OR "factory shutdown"'


class GdeltProvider(BaseSignalProvider):
    provider_name = "GDELT"

    def is_configured(self) -> bool:
        # GDELT v2 DOC API requires no private API key for basic article searches
        return True

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.provider_name,
            configured=True,
            status=ProviderStatus.SUCCESS,
            message="GDELT v2 public endpoint available (no API key required).",
        )

    def _normalize_item(self, item: dict, query: str) -> NormalizedSignal:
        url = str(item.get("url") or "")
        title = str(item.get("title") or "")
        sig = NormalizedSignal(
            signal_id=f"SIG-GDELT-{compute_content_hash('GDELT', url, title)}",
            provider="GDELT",
            canonical_url=url,
            title=title,
            description_or_snippet=None,
            publisher=item.get("domain"),
            published_at_utc=item.get("seendate"),
            retrieved_at_utc=utc_now_iso(),
            language=item.get("language", "English"),
            content_hash=compute_content_hash("GDELT", url, title),
            provenance="PUBLIC_REAL",
            provider_article_id=url,
            source_credibility=0.75,
            search_query=query,
        )
        return resolve_signal_entity(sig)

    def fetch_fixture(self) -> ProviderFetchResult:
        articles = FIXTURE_GDELT.get("articles", [])
        signals = [self._normalize_item(a, DEFAULT_QUERY) for a in articles]
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=True,
        )

    def fetch_live(self, query: str | None = None, limit: int = 25) -> ProviderFetchResult:
        q = query or DEFAULT_QUERY
        params = {
            "query": q,
            "mode": "ArtList",
            "format": "json",
            "sort": "DateDesc",
            "timespan": "7d",
            "maxrecords": min(limit, 50),
        }
        headers = {"User-Agent": "ProcuraX-Decision-Intelligence/1.0"}

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(GDELT_URL, params=params, headers=headers)
                if res.status_code == 429:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.RATE_LIMITED,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message="GDELT rate limit exceeded (HTTP 429).",
                    )
                if res.status_code >= 500:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.PROVIDER_UNAVAILABLE,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message=f"GDELT server error: HTTP {res.status_code}.",
                    )
                res.raise_for_status()
                data = res.json()
        except httpx.TimeoutException:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.TIMEOUT,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message="GDELT request timed out.",
            )
        except Exception as exc:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.INVALID_RESPONSE,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message=f"GDELT response parsing failed: {exc}",
            )

        articles = data.get("articles", []) if isinstance(data, dict) else []
        if not articles:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.NO_RESULTS,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
            )

        signals = [self._normalize_item(a, q) for a in articles]
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=False,
        )
