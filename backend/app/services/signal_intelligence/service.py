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

    def ingest_signals(
        self,
        query: str | None = None,
        providers: Sequence[str] | None = None,
        force_live: bool = False,
        persist: bool = True,
    ) -> list[NormalizedSignal]:
        """Fetch signals across providers, resolve entities, deduplicate, and persist."""
        use_live = force_live or settings.enable_live_signals
        selected = providers or list(self.providers.keys())

        collected_signals: list[NormalizedSignal] = []

        for p_name in selected:
            provider = self.providers.get(p_name)
            if not provider:
                continue

            result = provider.fetch(query=query, use_live=use_live)
            if result.status in {ProviderStatus.SUCCESS, ProviderStatus.PARTIAL_SUCCESS}:
                collected_signals.extend(result.normalized_signals)

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
