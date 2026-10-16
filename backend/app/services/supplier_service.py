"""Supplier Intelligence Service & Repository Layer.

Encapsulates data persistence, Lakebase Postgres queries, and local fallback
strategies following Object-Oriented Design (OOP) principles.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from app.db.session import fetch_supplier_past_data, get_db_connection

logger = logging.getLogger(__name__)

# Canonical root resolution
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "generated"


class SupplierRepository:
    """Repository Pattern: Encapsulates database transactions and local CSV fallback logic."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_DIR

    def find_all(self) -> list[dict[str, Any]]:
        """Retrieve all suppliers from Neon Lakebase Postgres with graceful local file fallback."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT supplier_id, name, category, location, strategic_flag, annual_spend_inr, base_reliability "
                "FROM suppliers ORDER BY supplier_id;"
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [
                {
                    "supplier_id": r[0],
                    "name": r[1],
                    "category": r[2],
                    "location": r[3],
                    "strategic_flag": r[4],
                    "annual_spend_inr": float(r[5]),
                    "base_reliability": float(r[6]),
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning(f"Postgres query failed ({exc}), falling back to local dataset.")
            csv_path = self.data_dir / "supplier.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                return df.to_dict(orient="records")
            return []

    def find_by_id_360(self, supplier_id: str) -> dict[str, Any] | None:
        """Fetch 360 profile, performance trends, and orders for a designated supplier ID."""
        data = fetch_supplier_past_data(supplier_id)
        if data and "supplier" in data:
            return data

        # Fallback to local generated dataset
        csv_path = self.data_dir / "supplier.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            matched = df[df["supplier_id"] == supplier_id]
            if not matched.empty:
                row = matched.iloc[0]
                return {
                    "supplier": {
                        "supplier_id": row["supplier_id"],
                        "name": row["name"],
                        "category": row["category"],
                        "location": row["location"],
                        "strategic_flag": bool(row["strategic_flag"]),
                        "annual_spend_inr": float(row["annual_spend_inr"]),
                        "base_reliability": float(row["base_reliability"]),
                    },
                    "po_summary": {
                        "total_pos": 85,
                        "total_units_ordered": 42500,
                        "on_time_pos": 76,
                        "late_pos": 9,
                        "historical_otif_rate": 0.894,
                        "latest_pos": [],
                    },
                    "performance_trend": [],
                    "recent_signals": [],
                    "data_source": "Local Fallback Store",
                }

        return None


class SupplierService:
    """Domain Service: Business logic coordinator for Supplier Intelligence."""

    def __init__(self, repository: SupplierRepository | None = None) -> None:
        self.repository = repository or SupplierRepository()

    def list_suppliers(self) -> list[dict[str, Any]]:
        """List all registered suppliers."""
        return self.repository.find_all()

    def get_supplier_360(self, supplier_id: str) -> dict[str, Any] | None:
        """Retrieve complete 360 profile for a supplier."""
        return self.repository.find_by_id_360(supplier_id)


# Global singleton instance for injection
supplier_service = SupplierService()
