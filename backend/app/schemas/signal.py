"""Pydantic schemas for Signal Intelligence API responses."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    signal_id: str
    provider: str
    title: str
    description_or_snippet: str | None = None
    canonical_url: str
    publisher: str | None = None
    published_at_utc: str | None = None
    retrieved_at_utc: str
    language: str = "en"
    provenance: str = "PUBLIC_REAL"
    # Entity Resolution
    mapped_supplier_id: str | None = None
    entity_name: str | None = None
    mapping_method: str = "none"
    mapping_confidence: float = 0.0
    scenario_disclaimer: str | None = None
    # Event & Sentiment attributes
    event_type: str = "general_news"
    event_severity: float = 0.0
    source_credibility: float = 0.5
    evidence_confidence: float = 0.5
    provider_sentiment_score: float | None = None
    provider_sentiment_label: str | None = None
    # Freshness & Persistence
    content_hash: str | None = None
    freshness_status: str = "fresh"
    age_hours: float | None = None
    persisted: bool = False
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class SignalListResponse(BaseModel):
    signals: list[SignalResponse]
    total: int
    scenario_banner: str = (
        "Illustrative ApexDrive case · synthetic internal operations · real public sources where available"
    )
    disclaimer: str = (
        "External signals are public real news or regulatory documents. "
        "Any mapping to fictional supplier SUP-1047 is an explicit demonstration scenario assumption."
    )


class ProviderHealthResponse(BaseModel):
    provider: str
    configured: bool
    status: str
    message: str
    last_fetched_at: str | None = None
    latency_ms: float | None = Field(None, description="Average response latency in milliseconds")
    circuit_breaker_status: str = Field("CLOSED", description="Circuit breaker state: CLOSED, OPEN, HALF_OPEN")
    freshness_window_hours: int = Field(24, description="Freshness threshold window in hours")
