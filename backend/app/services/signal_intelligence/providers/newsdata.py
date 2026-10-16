"""NewsData.io news API adapter."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.signal_intelligence.base_provider import BaseSignalProvider, utc_now_iso
from app.services.signal_intelligence.deduplication import compute_content_hash
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.fixtures import FIXTURE_NEWSDATA
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderFetchResult, ProviderHealth, ProviderStatus

NEWSDATA_URL = "https://newsdata.io/api/1/news"
DEFAULT_QUERY = "raw material shortage OR factory shutdown OR supply chain disruption"


class NewsDataProvider(BaseSignalProvider):
    provider_name = "NewsData.io"

    def is_configured(self) -> bool:
        return bool(settings.newsdata_api_key.strip())

    def health_check(self) -> ProviderHealth:
        configured = self.is_configured()
        return ProviderHealth(
            provider=self.provider_name,
            configured=configured,
            status=ProviderStatus.SUCCESS if configured else ProviderStatus.NOT_CONFIGURED,
            message="NewsData.io API key configured." if configured else "NEWSDATA_API_KEY not set in environment.",
        )

    def _normalize_item(self, article: dict, query: str) -> NormalizedSignal:
        url = str(article.get("link") or "")
        title = str(article.get("title") or "")
        desc = article.get("description")

        sig = NormalizedSignal(
            signal_id=f"SIG-ND-{compute_content_hash('NewsData', url, title)}",
            provider="NewsData.io",
            canonical_url=url,
            title=title,
            description_or_snippet=desc,
            publisher=article.get("source_id"),
            published_at_utc=article.get("pubDate"),
            retrieved_at_utc=utc_now_iso(),
            language=article.get("language", "en"),
            content_hash=compute_content_hash("NewsData", url, title),
            provenance="PUBLIC_REAL",
            provider_article_id=article.get("article_id"),
            source_credibility=0.70,
            search_query=query,
        )
        return resolve_signal_entity(sig)

    def fetch_fixture(self) -> ProviderFetchResult:
        results = FIXTURE_NEWSDATA.get("results", [])
        signals = [self._normalize_item(a, DEFAULT_QUERY) for a in results]
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=True,
        )

    def fetch_live(self, query: str | None = None, limit: int = 10) -> ProviderFetchResult:
        key = settings.newsdata_api_key.strip()
        q = query or DEFAULT_QUERY
        params = {"apikey": key, "q": q, "language": "en"}

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(NEWSDATA_URL, params=params)
                if res.status_code in {401, 403}:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.NOT_CONFIGURED,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message="Invalid NewsData.io API key.",
                    )
                if res.status_code == 429:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.RATE_LIMITED,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message="NewsData.io rate limit reached.",
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
                error_message="NewsData.io request timed out.",
            )
        except Exception as exc:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.ERROR,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message=f"NewsData.io fetch failed: {exc}",
            )

        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.NO_RESULTS,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
            )

        signals = [self._normalize_item(a, q) for a in results[:limit]]
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=False,
        )
