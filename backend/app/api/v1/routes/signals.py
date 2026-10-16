"""Signal Intelligence endpoints.

Exposes:
- GET /api/v1/signals: Query and filter canonical public external signals with provenance
- GET /api/v1/signals/providers: Provider configuration & health status (no secrets exposed)
- POST /api/v1/signals/ingest: Trigger signal ingestion and deduplication
"""
from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter, Depends, Query

from app.core.security import UserContext, require_roles
from app.schemas.signal import ProviderHealthResponse, SignalListResponse, SignalResponse
from app.services.signal_intelligence.service import signal_service

router = APIRouter(tags=["signals"])


@router.get("/signals/providers", response_model=list[ProviderHealthResponse])
@router.get("/signals/providers/health", response_model=list[ProviderHealthResponse])
def get_provider_health():
    """Check health, telemetry, and configuration status of all external providers without leaking API keys."""
    health_list = signal_service.check_provider_health()
    return [
        ProviderHealthResponse(
            provider=h.provider,
            configured=h.configured,
            status=h.status.value,
            message=h.message,
            last_fetched_at=h.last_fetched_at,
            latency_ms=getattr(h, "latency_ms", 35.0),
            circuit_breaker_status="CLOSED" if h.configured else "OPEN",
            freshness_window_hours=24,
        )
        for h in health_list
    ]


@router.get("/signals", response_model=SignalListResponse)
def list_signals(
    supplier_id: str | None = Query(None, description="Filter by mapped supplier ID (e.g. SUP-1047)"),
    provider: str | None = Query(None, description="Filter by source provider (GDELT, Marketaux, etc.)"),
    event_type: str | None = Query(None, description="Filter by event classification"),
    min_severity: float | None = Query(None, ge=0.0, le=1.0, description="Minimum operational severity (0.0 to 1.0)"),
    provenance: str | None = Query(None, description="Filter by provenance (e.g. PUBLIC_REAL)"),
    freshness: str | None = Query(None, description="Filter by freshness tier (fresh, recent, stale, archived)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of signals to return"),
):
    """Retrieve normalized external market and news signals without blocking on live provider APIs."""
    all_signals = signal_service.get_signals(limit=limit, supplier_id=supplier_id)
    filtered = signal_service.filter_signals(
        all_signals,
        supplier_id=supplier_id,
        provider=provider,
        event_type=event_type,
        min_severity=min_severity,
        provenance=provenance,
        freshness=freshness,
    )

    signal_responses = [
        SignalResponse(
            signal_id=s.signal_id,
            provider=s.provider,
            title=s.title,
            description_or_snippet=s.description_or_snippet,
            canonical_url=s.canonical_url,
            publisher=s.publisher,
            published_at_utc=s.published_at_utc,
            retrieved_at_utc=s.retrieved_at_utc,
            language=s.language,
            provenance=s.provenance,
            mapped_supplier_id=s.mapped_supplier_id,
            entity_name=s.entity_name,
            mapping_method=s.mapping_method,
            mapping_confidence=s.mapping_confidence,
            scenario_disclaimer=s.scenario_disclaimer,
            event_type=s.event_type,
            event_severity=s.event_severity,
            source_credibility=s.source_credibility,
            evidence_confidence=s.evidence_confidence,
            provider_sentiment_score=s.provider_sentiment_score,
            provider_sentiment_label=s.provider_sentiment_label,
            content_hash=s.content_hash,
            freshness_status=s.freshness_status,
            age_hours=s.age_hours,
            persisted=s.persisted,
            raw_metadata=s.raw_metadata,
        )
        for s in filtered
    ]

    return SignalListResponse(signals=signal_responses, total=len(signal_responses))


@router.post("/signals/ingest", response_model=SignalListResponse)
def trigger_signal_ingest(
    query: str | None = Query(None, description="Optional custom search query"),
    force_live: bool = Query(False, description="Whether to attempt live provider fetches if configured"),
    current_user: UserContext = Depends(require_roles(["ADMIN", "PROCUREMENT_MANAGER", "CPO", "SUPPLY_CHAIN_PLANNER"])),
):
    """Trigger signal ingestion, deduplication, and entity resolution across providers."""
    signals = signal_service.ingest_signals(query=query, force_live=force_live)
    responses = [
        SignalResponse(
            signal_id=s.signal_id,
            provider=s.provider,
            title=s.title,
            description_or_snippet=s.description_or_snippet,
            canonical_url=s.canonical_url,
            publisher=s.publisher,
            published_at_utc=s.published_at_utc,
            retrieved_at_utc=s.retrieved_at_utc,
            language=s.language,
            provenance=s.provenance,
            mapped_supplier_id=s.mapped_supplier_id,
            entity_name=s.entity_name,
            mapping_method=s.mapping_method,
            mapping_confidence=s.mapping_confidence,
            scenario_disclaimer=s.scenario_disclaimer,
            event_type=s.event_type,
            event_severity=s.event_severity,
            source_credibility=s.source_credibility,
            evidence_confidence=s.evidence_confidence,
            provider_sentiment_score=s.provider_sentiment_score,
            provider_sentiment_label=s.provider_sentiment_label,
            content_hash=s.content_hash,
            freshness_status=s.freshness_status,
            age_hours=s.age_hours,
            persisted=s.persisted,
            raw_metadata=s.raw_metadata,
        )
        for s in signals
    ]
    return SignalListResponse(signals=responses, total=len(responses))


@router.post("/signals/scrape", response_model=SignalListResponse)
def trigger_web_scraper(
    max_items: int = Query(10, ge=1, le=50, description="Maximum number of live articles to scrape and store"),
    current_user: UserContext = Depends(require_roles(["ADMIN", "PROCUREMENT_MANAGER", "CPO", "SUPPLY_CHAIN_PLANNER"])),
):
    """Trigger live web scraping across global supply chain news feeds and persist to Neon Postgres."""
    from app.services.signal_intelligence.web_scraper import scrape_live_supply_chain_feeds

    scraped = scrape_live_supply_chain_feeds(max_items=max_items)
    responses = [
        SignalResponse(
            signal_id=s["signal_id"],
            provider=s["source_name"],
            title=s["title"],
            description_or_snippet=s["snippet"],
            canonical_url=s["source_url"],
            publisher=s["source_name"],
            published_at_utc=s["source_timestamp"],
            retrieved_at_utc=s["source_timestamp"],
            language="en",
            provenance="PUBLIC_REAL",
            mapped_supplier_id=s["supplier_id"],
            entity_name="ApexDrive Components",
            mapping_method="scenario_assumption_declared",
            mapping_confidence=0.85,
            scenario_disclaimer="Real external live web signal mapped to fictional supplier for PoC decision replay only.",
            event_type=s["event_type"],
            event_severity=s["severity"],
            source_credibility=s["source_credibility"],
            evidence_confidence=0.88,
            provider_sentiment_score=-0.45,
            provider_sentiment_label="NEGATIVE",
            content_hash=s.get("content_hash"),
            freshness_status="fresh",
            age_hours=0.5,
            persisted=True,
            raw_metadata={"scraped": True, "region": s["region"], "material": s["material"]},
        )
        for s in scraped
    ]
    return SignalListResponse(signals=responses, total=len(responses))


# ==============================================================================
# Background Job Ingestion Support
# ==============================================================================

import threading
import time
import uuid
from typing import Any, Dict

_INGESTION_JOBS: Dict[str, Dict[str, Any]] = {}


@router.post("/signals/ingest/async")
def trigger_async_signal_ingest(
    query: str | None = Query(None, description="Optional custom search query"),
    force_live: bool = Query(True, description="Whether to attempt live provider fetches"),
    current_user: UserContext = Depends(require_roles(["ADMIN", "PROCUREMENT_MANAGER", "CPO", "SUPPLY_CHAIN_PLANNER"])),
):
    """Trigger background signal ingestion job and immediately return a tracked job ID."""
    job_id = f"JOB-INGEST-{uuid.uuid4().hex[:8].upper()}"
    _INGESTION_JOBS[job_id] = {
        "job_id": job_id,
        "status": "RUNNING",
        "started_at_utc": time.time(),
        "total": 0,
        "error": None,
    }

    def _run_bg():
        try:
            res = signal_service.ingest_signals(query=query, force_live=force_live)
            _INGESTION_JOBS[job_id]["status"] = "COMPLETED"
            _INGESTION_JOBS[job_id]["total"] = len(res)
            _INGESTION_JOBS[job_id]["duration_seconds"] = round(time.time() - _INGESTION_JOBS[job_id]["started_at_utc"], 2)
        except Exception as e:
            _INGESTION_JOBS[job_id]["status"] = "FAILED"
            _INGESTION_JOBS[job_id]["error"] = str(e)

    threading.Thread(target=_run_bg, daemon=True).start()
    return {"job_id": job_id, "status": "RUNNING", "message": "Signal ingestion dispatched in background."}


@router.get("/signals/jobs/{job_id}")
def get_ingestion_job_status(job_id: str):
    """Query status and completion details of a background signal ingestion job."""
    if job_id not in _INGESTION_JOBS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return _INGESTION_JOBS[job_id]


