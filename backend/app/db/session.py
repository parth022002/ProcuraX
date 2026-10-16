"""Database connection and health checks for Neon Lakebase Postgres."""
from __future__ import annotations

import time
from typing import Any, Dict
import psycopg2
from app.core.config import settings


def get_db_connection() -> psycopg2.extensions.connection:
    """Return an active connection to Neon Lakebase Postgres."""
    if not settings.database_url:
        raise ValueError("DATABASE_URL is not configured.")
    return psycopg2.connect(settings.database_url, connect_timeout=5)


def check_db_health() -> Dict[str, Any]:
    """Verify live connectivity and measure latency to Neon Lakebase Postgres."""
    if not settings.database_url:
        return {
            "status": "unconfigured",
            "provider": "Neon Postgres",
            "message": "DATABASE_URL not set in environment.",
        }

    start = time.time()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        pg_version = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM suppliers;")
        supplier_count = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM skus;")
        sku_count = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM inventory;")
        inv_count = cur.fetchone()[0]

        cur.close()
        conn.close()
        latency_ms = (time.time() - start) * 1000

        return {
            "status": "healthy",
            "provider": "Neon Lakebase Postgres",
            "version": pg_version,
            "latency_ms": round(latency_ms, 2),
            "counts": {
                "suppliers": supplier_count,
                "skus": sku_count,
                "inventory": inv_count,
            },
        }
    except Exception as exc:
        return {
            "status": "error",
            "provider": "Neon Lakebase Postgres",
            "error": str(exc),
            "latency_ms": round((time.time() - start) * 1000, 2),
        }


def persist_case_record(case_id: str, supplier_id: str, status: str, metadata: dict | None = None) -> bool:
    """Persist or update a disruption case record in Neon Lakebase Postgres."""
    if not settings.database_url:
        return False
    try:
        import json
        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cases (case_id, supplier_id, opened_at, status, prediction_as_of, metadata)
            VALUES (%s, %s, now(), %s, now(), %s)
            ON CONFLICT (case_id) DO UPDATE SET
                status = EXCLUDED.status,
                metadata = EXCLUDED.metadata;
            """,
            (case_id, supplier_id, status, json.dumps(metadata or {})),
        )
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


def fetch_supplier_past_data(supplier_id: str) -> Dict[str, Any]:
    """Fetch comprehensive historical data for a supplier from Neon Lakebase Postgres."""
    if not settings.database_url:
        return {}

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Supplier master
        cur.execute(
            """
            SELECT supplier_id, name, category, location, strategic_flag, annual_spend_inr, base_reliability
            FROM suppliers WHERE supplier_id = %s;
            """,
            (supplier_id,),
        )
        s_row = cur.fetchone()
        if not s_row:
            cur.close()
            conn.close()
            return {}

        supplier_meta = {
            "supplier_id": s_row[0],
            "name": s_row[1],
            "category": s_row[2],
            "location": s_row[3],
            "strategic_flag": s_row[4],
            "annual_spend_inr": float(s_row[5]),
            "base_reliability": float(s_row[6]),
        }

        # 2. Historical PO metrics
        cur.execute(
            """
            SELECT
                count(*) as total_pos,
                sum(quantity) as total_units_ordered,
                sum(CASE WHEN status = 'delivered_on_time' THEN 1 ELSE 0 END) as on_time_pos,
                sum(CASE WHEN status = 'delivered_late' THEN 1 ELSE 0 END) as late_pos
            FROM purchase_orders
            WHERE supplier_id = %s;
            """,
            (supplier_id,),
        )
        po_row = cur.fetchone()
        total_pos = po_row[0] or 0
        total_units = po_row[1] or 0
        on_time_pos = po_row[2] or 0
        late_pos = po_row[3] or 0
        historical_otif_rate = round(on_time_pos / total_pos, 4) if total_pos > 0 else 0.95

        # Latest 5 POs
        cur.execute(
            """
            SELECT po_id, sku_id, quantity, order_date, promised_date, status
            FROM purchase_orders
            WHERE supplier_id = %s
            ORDER BY order_date DESC LIMIT 5;
            """,
            (supplier_id,),
        )
        latest_pos = [
            {
                "po_id": r[0],
                "sku_id": r[1],
                "quantity": r[2],
                "order_date": str(r[3]),
                "promised_date": str(r[4]),
                "status": r[5],
            }
            for r in cur.fetchall()
        ]

        # 3. Monthly Performance Trend (OTIF, defects, capacity utilization)
        cur.execute(
            """
            SELECT period_date, otif, lead_time_days, defect_rate, capacity_utilisation
            FROM supplier_performance
            WHERE supplier_id = %s
            ORDER BY period_date ASC;
            """,
            (supplier_id,),
        )
        performance_trend = [
            {
                "period": str(r[0]),
                "otif": float(r[1]),
                "lead_time_days": float(r[2]),
                "defect_rate": float(r[3]),
                "capacity_utilisation": float(r[4]),
            }
            for r in cur.fetchall()
        ]

        # 4. Associated historical signals
        cur.execute(
            """
            SELECT signal_id, source_name, event_type, severity, source_credibility
            FROM external_signals
            WHERE supplier_id = %s
            ORDER BY source_timestamp DESC LIMIT 5;
            """,
            (supplier_id,),
        )
        recent_signals = [
            {
                "signal_id": r[0],
                "source": r[1],
                "event_type": r[2],
                "severity": float(r[3]),
                "credibility": float(r[4]),
            }
            for r in cur.fetchall()
        ]

        cur.close()
        conn.close()

        return {
            "supplier": supplier_meta,
            "po_summary": {
                "total_pos": total_pos,
                "total_units_ordered": total_units,
                "on_time_pos": on_time_pos,
                "late_pos": late_pos,
                "historical_otif_rate": historical_otif_rate,
                "latest_pos": latest_pos,
            },
            "performance_trend": performance_trend,
            "recent_signals": recent_signals,
            "data_source": "Neon Lakebase Postgres (Historical Store)",
        }
    except Exception as exc:
        return {"error": str(exc)}


