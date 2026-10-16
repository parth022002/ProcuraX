"""Central Signal Intelligence orchestration service with persistence and deduplication."""
from __future__ import annotations

import logging
from typing import Sequence

from app.core.config import settings
from app.services.signal_intelligence.base_provider import BaseSignalProvider
from app.services.signal_intelligence.deduplication import deduplicate_signals
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.freshness import calculate_signal_freshness
from app.services.signal_intelligence.providers.alpha_vantage import AlphaVantageProvider
from app.services.signal_intelligence.providers.gdelt import GdeltProvider
from app.services.signal_intelligence.providers.marketaux import MarketauxProvider
from app.services.signal_intelligence.providers.newsdata import NewsDataProvider
from app.services.signal_intelligence.providers.sec_edgar import SecEdgarProvider
from app.services.signal_intelligence.repository import SignalRepository
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderHealth, ProviderStatus

logger = logging.getLogger(__name__)


class SignalIntelligenceService:
    """Orchestrates public signal intelligence ingestion, deduplication, entity resolution, and persistence."""

    def __init__(self, repository: SignalRepository | None = None):
        self.providers: dict[str, BaseSignalProvider] = {
            "GDELT": GdeltProvider(),
            "Marketaux": MarketauxProvider(),
            "Alpha Vantage": AlphaVantageProvider(),
            "NewsData.io": NewsDataProvider(),
            "SEC EDGAR": SecEdgarProvider(),
        }
        self.repository = repository or SignalRepository()

    def check_provider_health(self) -> list[ProviderHealth]:
        """Audit configuration and health status of all registered providers without leaking secrets."""
        health_reports: list[ProviderHealth] = []
        for provider in self.providers.values():
            h = provider.health_check()
            if not h.last_fetched_at and provider.last_fetched_at:
                h.last_fetched_at = provider.last_fetched_at
            health_reports.append(h)
        return health_reports

    def get_signals(self, limit: int = 50, supplier_id: str | None = None) -> list[NormalizedSignal]:
        """Fetch saved signals from persistent store or cache without blocking on external provider APIs."""
        if self.repository.is_available():
            try:
                persisted = self.repository.fetch_persisted_signals(supplier_id=supplier_id, limit=limit)
                if persisted:
                    return persisted
            except Exception as exc:
                logger.warning("Failed to fetch persisted signals from repository: %s", exc)

        # Fallback to deterministic offline fixtures (instant execution, zero external network delay)
        return self.ingest_signals(force_live=False, persist=False)

    def ingest_signals(
        self,
        query: str | None = None,
        providers: Sequence[str] | None = None,
        force_live: bool = False,
        persist: bool = True,
    ) -> list[NormalizedSignal]:
        """Fetch signals across providers concurrently, resolve entities, deduplicate, and persist."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        use_live = force_live or settings.enable_live_signals
        selected = providers or list(self.providers.keys())

        collected_signals: list[NormalizedSignal] = []

        def _fetch_single_provider(p_name: str) -> list[NormalizedSignal]:
            provider = self.providers.get(p_name)
            if not provider:
                return []
            try:
                res = provider.fetch(query=query, use_live=use_live)
                if res.status in {ProviderStatus.SUCCESS, ProviderStatus.PARTIAL_SUCCESS}:
                    return res.normalized_signals
            except Exception as exc:
                logger.warning("Provider '%s' fetch error: %s", p_name, exc)
            return []

        # Concurrently fetch from external providers to avoid serial latency buildup
        with ThreadPoolExecutor(max_workers=min(len(selected), 5)) as executor:
            future_to_provider = {
                executor.submit(_fetch_single_provider, p_name): p_name
                for p_name in selected
            }
            for future in as_completed(future_to_provider):
                p_name = future_to_provider[future]
                try:
                    sigs = future.result(timeout=10.0)
                    collected_signals.extend(sigs)
                except Exception as exc:
                    logger.warning("Provider '%s' execution timed out or failed: %s", p_name, exc)

        # Entity resolution & scenario mapping
        resolved = [resolve_signal_entity(s) for s in collected_signals]

        # Content-hash deduplication
        deduped = deduplicate_signals(resolved)

        # Freshness calculation
        for s in deduped:
            s_tier, s_age = calculate_signal_freshness(s.published_at_utc or s.retrieved_at_utc)
            s.freshness_status = s_tier
            s.age_hours = s_age

        # Persist to PostgreSQL if configured
        if persist and self.repository.is_available():
            persisted_count = self.repository.persist_signals(deduped)
            logger.info("Persisted %d signals to PostgreSQL store.", persisted_count)

        # Sort descending by published/retrieved time
        return sorted(
            deduped,
            key=lambda s: s.published_at_utc or s.retrieved_at_utc or "",
            reverse=True,
        )

    def filter_signals(
        self,
        signals: list[NormalizedSignal],
        supplier_id: str | None = None,
        provider: str | None = None,
        event_type: str | None = None,
        min_severity: float | None = None,
        provenance: str | None = None,
        freshness: str | None = None,
    ) -> list[NormalizedSignal]:
        """Apply user or workflow filters to in-memory signals."""
        filtered = signals

        if supplier_id:
            filtered = [s for s in filtered if s.mapped_supplier_id == supplier_id]
        if provider:
            filtered = [s for s in filtered if s.provider.lower() == provider.lower()]
        if event_type:
            filtered = [s for s in filtered if s.event_type == event_type]
        if min_severity is not None:
            filtered = [s for s in filtered if s.event_severity >= min_severity]
        if provenance:
            filtered = [s for s in filtered if s.provenance == provenance]
        if freshness:
            filtered = [s for s in filtered if s.freshness_status == freshness]

        return filtered


signal_service = SignalIntelligenceService()
