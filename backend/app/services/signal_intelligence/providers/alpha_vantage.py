"""Alpha Vantage News Sentiment API adapter."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.signal_intelligence.base_provider import BaseSignalProvider, utc_now_iso
from app.services.signal_intelligence.deduplication import compute_content_hash
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.fixtures import FIXTURE_ALPHA_VANTAGE
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderFetchResult, ProviderHealth, ProviderStatus

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
DEFAULT_TOPICS = "manufacturing,technology"


class AlphaVantageProvider(BaseSignalProvider):
    provider_name = "Alpha Vantage"

    def is_configured(self) -> bool:
        return bool(settings.alpha_vantage_api_key.strip())

    def health_check(self) -> ProviderHealth:
        configured = self.is_configured()
        return ProviderHealth(
            provider=self.provider_name,
            configured=configured,
            status=ProviderStatus.SUCCESS if configured else ProviderStatus.NOT_CONFIGURED,
            message="Alpha Vantage API key configured." if configured else "ALPHA_VANTAGE_API_KEY not set in environment.",
        )

    def _normalize_item(self, article: dict, query: str) -> NormalizedSignal:
        url = str(article.get("url") or "")
        title = str(article.get("title") or "")
        summary = article.get("summary")

        sig = NormalizedSignal(
            signal_id=f"SIG-AV-{compute_content_hash('AlphaVantage', url, title)}",
            provider="Alpha Vantage",
            canonical_url=url,
            title=title,
            description_or_snippet=summary,
            publisher=article.get("source"),
            published_at_utc=article.get("time_published"),
            retrieved_at_utc=utc_now_iso(),
            language=article.get("language", "en"),
            content_hash=compute_content_hash("AlphaVantage", url, title),
            provenance="PUBLIC_REAL",
            provider_article_id=url,
            provider_sentiment_score=article.get("overall_sentiment_score"),
            provider_sentiment_label=article.get("overall_sentiment_label"),
            source_credibility=0.85,
            search_query=query,
        )
        return resolve_signal_entity(sig)

    def fetch_fixture(self) -> ProviderFetchResult:
        feed = FIXTURE_ALPHA_VANTAGE.get("feed", [])
        signals = [self._normalize_item(a, DEFAULT_TOPICS) for a in feed]
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=True,
        )

    def fetch_live(self, query: str | None = None, limit: int = 50) -> ProviderFetchResult:
        key = settings.alpha_vantage_api_key.strip()
        topics = query or DEFAULT_TOPICS
        params = {
            "function": "NEWS_SENTIMENT",
            "topics": topics,
            "limit": min(limit, 50),
            "sort": "LATEST",
            "apikey": key,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(ALPHA_VANTAGE_URL, params=params)
                res.raise_for_status()
                data = res.json()
        except httpx.TimeoutException:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.TIMEOUT,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message="Alpha Vantage request timed out.",
            )
        except Exception as exc:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.ERROR,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message=f"Alpha Vantage fetch failed: {exc}",
            )

        if isinstance(data, dict):
            if "Note" in data or "Information" in data:
                return ProviderFetchResult(
                    provider=self.provider_name,
                    status=ProviderStatus.RATE_LIMITED,
                    fetched_at_utc=utc_now_iso(),
                    result_count=0,
                    normalized_signals=[],
                    error_message=f"Alpha Vantage API limit notice: {data.get('Note') or data.get('Information')}",
                )
            if "Error Message" in data:
                return ProviderFetchResult(
                    provider=self.provider_name,
                    status=ProviderStatus.NOT_CONFIGURED,
                    fetched_at_utc=utc_now_iso(),
                    result_count=0,
                    normalized_signals=[],
                    error_message=f"Alpha Vantage error: {data['Error Message']}",
                )

        feed = data.get("feed", []) if isinstance(data, dict) else []
        if not feed:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.NO_RESULTS,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
            )

        signals = [self._normalize_item(a, topics) for a in feed]
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=False,
        )
