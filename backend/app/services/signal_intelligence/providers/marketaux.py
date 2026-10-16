"""Marketaux news & sentiment API adapter."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.signal_intelligence.base_provider import BaseSignalProvider, utc_now_iso
from app.services.signal_intelligence.deduplication import compute_content_hash
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.fixtures import FIXTURE_MARKETAUX
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderFetchResult, ProviderHealth, ProviderStatus

MARKETAUX_URL = "https://api.marketaux.com/v1/news/all"
DEFAULT_SEARCH = 'supplier | "supply chain" | semiconductor | logistics | "factory shutdown" | "port disruption"'


class MarketauxProvider(BaseSignalProvider):
    provider_name = "Marketaux"

    def is_configured(self) -> bool:
        return bool(settings.marketaux_api_token.strip())

    def health_check(self) -> ProviderHealth:
        configured = self.is_configured()
        return ProviderHealth(
            provider=self.provider_name,
            configured=configured,
            status=ProviderStatus.SUCCESS if configured else ProviderStatus.NOT_CONFIGURED,
            message="Marketaux API token configured." if configured else "MARKETAUX_API_TOKEN not set in environment.",
        )

    def _normalize_item(self, article: dict, query: str) -> list[NormalizedSignal]:
        url = str(article.get("url") or "")
        title = str(article.get("title") or "")
        desc = article.get("description") or article.get("snippet")
        entities = article.get("entities") or []

        signals = []
        if not entities:
            sig = NormalizedSignal(
                signal_id=f"SIG-MKT-{compute_content_hash('Marketaux', url, title)}",
                provider="Marketaux",
                canonical_url=url,
                title=title,
                description_or_snippet=desc,
                publisher=article.get("source"),
                published_at_utc=article.get("published_at"),
                retrieved_at_utc=utc_now_iso(),
                language=article.get("language", "en"),
                content_hash=compute_content_hash("Marketaux", url, title),
                provenance="PUBLIC_REAL",
                provider_article_id=article.get("uuid"),
                source_credibility=0.80,
                search_query=query,
            )
            signals.append(resolve_signal_entity(sig))
        else:
            for ent in entities:
                ent_name = ent.get("name")
                sig = NormalizedSignal(
                    signal_id=f"SIG-MKT-{compute_content_hash('Marketaux', url, f'{title}_{ent_name}')}",
                    provider="Marketaux",
                    canonical_url=url,
                    title=title,
                    description_or_snippet=desc,
                    publisher=article.get("source"),
                    published_at_utc=article.get("published_at"),
                    retrieved_at_utc=utc_now_iso(),
                    language=article.get("language", "en"),
                    content_hash=compute_content_hash("Marketaux", url, title),
                    provenance="PUBLIC_REAL",
                    provider_article_id=article.get("uuid"),
                    entity_name=ent_name,
                    entity_symbol=ent.get("symbol"),
                    entity_match_score=ent.get("match_score"),
                    provider_sentiment_score=ent.get("sentiment_score"),
                    source_credibility=0.85,
                    search_query=query,
                )
                signals.append(resolve_signal_entity(sig))

        return signals

    def fetch_fixture(self) -> ProviderFetchResult:
        articles = FIXTURE_MARKETAUX.get("data", [])
        signals: list[NormalizedSignal] = []
        for a in articles:
            signals.extend(self._normalize_item(a, DEFAULT_SEARCH))
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=True,
        )

    def fetch_live(self, query: str | None = None, limit: int = 3) -> ProviderFetchResult:
        token = settings.marketaux_api_token.strip()
        q = query or DEFAULT_SEARCH
        params = {
            "api_token": token,
            "search": q,
            "language": "en",
            "limit": min(limit, 3),  # Free tier allows 3 per request
            "must_have_entities": "true",
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(MARKETAUX_URL, params=params)
                if res.status_code in {401, 403}:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.NOT_CONFIGURED,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message="Invalid Marketaux API token (HTTP 401/403).",
                    )
                if res.status_code == 429:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.RATE_LIMITED,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message="Marketaux rate limit/quota reached (HTTP 429).",
                    )
                if res.status_code >= 500:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.PROVIDER_UNAVAILABLE,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message=f"Marketaux server error (HTTP {res.status_code}).",
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
                error_message="Marketaux request timed out.",
            )
        except Exception as exc:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.ERROR,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message=f"Marketaux fetch failed: {exc}",
            )

        articles = data.get("data", []) if isinstance(data, dict) else []
        if not articles:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.NO_RESULTS,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
            )

        signals = []
        for a in articles:
            signals.extend(self._normalize_item(a, q))

        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=False,
        )
