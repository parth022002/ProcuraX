"""PostgreSQL persistence repository for external signals."""
from __future__ import annotations

import json
import logging
from typing import Sequence
import psycopg2
from psycopg2.extras import execute_batch

from app.core.config import settings
from app.db.session import get_db_connection
from app.services.signal_intelligence.freshness import calculate_signal_freshness
from app.services.signal_intelligence.schema import NormalizedSignal

logger = logging.getLogger(__name__)


class SignalRepository:
    """Repository managing idempotent persistence and querying of normalized signals in PostgreSQL."""

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url if db_url is not None else settings.database_url

    def is_available(self) -> bool:
        return bool(self.db_url)

    def persist_signals(self, signals: Sequence[NormalizedSignal]) -> int:
        """Idempotently persist normalized signals into PostgreSQL external_signals table."""
        if not self.is_available() or not signals:
            return 0

        rows = []
        for s in signals:
            # Recalculate freshness prior to persistence
            status, age_hours = calculate_signal_freshness(s.published_at_utc or s.retrieved_at_utc)
            s.freshness_status = status
            s.age_hours = age_hours

            provenance_payload = json.dumps(
                {
                    "provenance_class": s.provenance,
                    "mapping_method": s.mapping_method,
                    "mapping_confidence": s.mapping_confidence,
                    "scenario_disclaimer": s.scenario_disclaimer,
                    "evidence_confidence": s.evidence_confidence,
                    "raw_metadata": s.raw_metadata,
                }
            )

            rows.append(
                (
                    s.signal_id,
                    s.provider,
                    s.canonical_url,
                    s.published_at_utc or s.retrieved_at_utc,
                    s.event_type,
                    s.mapped_supplier_id,
                    s.event_severity,
                    s.source_credibility,
                    False,  # is_synthetic (signals are PUBLIC_REAL with scenario mappings)
                    provenance_payload,
                    s.content_hash,
                    s.canonical_url,
                    s.freshness_status,
                    s.age_hours,
                )
            )

        insert_sql = """
            INSERT INTO external_signals (
                signal_id, source_name, source_url, source_timestamp,
                event_type, supplier_id, severity, source_credibility,
                is_synthetic, provenance, content_hash, canonical_url,
                freshness_status, age_hours, persisted_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (signal_id) DO UPDATE SET
                severity = EXCLUDED.severity,
                source_credibility = EXCLUDED.source_credibility,
                content_hash = EXCLUDED.content_hash,
                freshness_status = EXCLUDED.freshness_status,
                age_hours = EXCLUDED.age_hours,
                provenance = EXCLUDED.provenance,
                persisted_at = now();
        """

        try:
            conn = get_db_connection()
            conn.autocommit = True
            with conn.cursor() as cur:
                execute_batch(cur, insert_sql, rows, page_size=50)
            conn.close()

            # Mark in-memory signals as persisted
            for s in signals:
                s.persisted = True
            return len(rows)
        except Exception as exc:
            logger.warning("SignalRepository persistence bypassed (DB unavailable or error): %s", exc)
            return 0

    def fetch_persisted_signals(
        self,
        supplier_id: str | None = None,
        limit: int = 50,
    ) -> list[NormalizedSignal]:
        """Fetch persisted signals from external_signals table."""
        if not self.is_available():
            return []

        query = """
            SELECT
                signal_id, source_name, canonical_url, source_url,
                source_timestamp, event_type, supplier_id, severity,
                source_credibility, provenance, content_hash,
                freshness_status, age_hours
            FROM external_signals
        """
        params: list[object] = []
        if supplier_id:
            query += " WHERE supplier_id = %s"
            params.append(supplier_id)
        query += " ORDER BY source_timestamp DESC LIMIT %s;"
        params.append(limit)

        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                raw_rows = cur.fetchall()
            conn.close()

            results: list[NormalizedSignal] = []
            for r in raw_rows:
                raw_meta = r[9]
                if isinstance(raw_meta, dict):
                    meta = raw_meta
                elif isinstance(raw_meta, str):
                    try:
                        meta = json.loads(raw_meta)
                    except Exception:
                        meta = {}
                else:
                    meta = {}

                disclaimer = meta.get("scenario_disclaimer")
                if not disclaimer and r[6] == "SUP-1047":
                    disclaimer = "Real external public signal mapped to fictional supplier SUP-1047 for PoC decision replay."
                results.append(
                    NormalizedSignal(
                        signal_id=r[0],
                        provider=r[1],
                        canonical_url=r[2] or r[3] or "",
                        title=meta.get("title", f"Signal {r[0]}"),
                        description_or_snippet=meta.get("snippet"),
                        publisher=r[1],
                        published_at_utc=str(r[4]) if r[4] else None,
                        retrieved_at_utc=str(r[4]) if r[4] else "",
                        language="en",
                        content_hash=r[10] or "",
                        provenance=meta.get("provenance_class", "PUBLIC_REAL"),
                        mapped_supplier_id=r[6],
                        mapping_method=meta.get("mapping_method", "none"),
                        mapping_confidence=meta.get("mapping_confidence", 0.0),
                        scenario_disclaimer=disclaimer,
                        event_type=r[5],
                        event_severity=float(r[7]) if r[7] is not None else 0.0,
                        source_credibility=float(r[8]) if r[8] is not None else 0.70,
                        freshness_status=r[11] or "fresh",
                        age_hours=float(r[12]) if r[12] is not None else None,
                        persisted=True,
                        raw_metadata=meta.get("raw_metadata", {}),
                    )
                )
            return results
        except Exception as exc:
            logger.warning("SignalRepository query failed: %s", exc)
            return []
