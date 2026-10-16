"""Canonical signal intelligence schemas and typed provider interfaces."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    NO_RESULTS = "no_results"
    NOT_CONFIGURED = "not_configured"
    RATE_LIMITED = "rate_limited"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    ERROR = "error"


@dataclass
class NormalizedSignal:
    signal_id: str
    provider: str
    canonical_url: str
    title: str
    description_or_snippet: str | None
    publisher: str | None
    published_at_utc: str | None
    retrieved_at_utc: str
    language: str
    content_hash: str
    provenance: str = "PUBLIC_REAL"  # PUBLIC_REAL | SYNTHETIC | DERIVED | ILLUSTRATIVE
    provider_article_id: str | None = None
    # Entity Resolution & Scenario Mapping
    entity_name: str | None = None
    entity_symbol: str | None = None
    entity_match_score: float | None = None
    mapped_supplier_id: str | None = None
    mapping_method: str = "none"  # "scenario_assumption" | "exact_name" | "none"
    mapping_confidence: float = 0.0
    scenario_disclaimer: str | None = None
    # Sentiment & Event Attributes
    provider_sentiment_score: float | None = None
    provider_sentiment_label: str | None = None
    event_type: str = "general_news"
    event_severity: float = 0.0  # 0.0 to 1.0 (or 0.0 to 10.0 mapped)
    source_credibility: float = 0.70  # Tier rating: government/official > news > forum
    evidence_confidence: float = 0.50
    search_query: str | None = None
    # Freshness & Persistence
    freshness_status: str = "fresh"  # "fresh" (<24h) | "recent" (<72h) | "stale" (<7d) | "archived" (>=7d)
    age_hours: float | None = None
    persisted: bool = False
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderFetchResult:
    provider: str
    status: ProviderStatus
    fetched_at_utc: str
    result_count: int
    normalized_signals: list[NormalizedSignal]
    error_message: str | None = None
    is_mock: bool = False


@dataclass
class ProviderHealth:
    provider: str
    configured: bool
    status: ProviderStatus
    message: str
    last_fetched_at: str | None = None
