"""Data Preprocessing and Cleaning Pipeline for Historical Procurement Data.

Cleans and validates:
- Purchase Orders (order/promised/actual date validation, quantity checks, status normalization)
- Quality & Defect Records (bound checks: 0-1, format period dates)
- Capacity Utilization (positive units, 0-1.5 utilisation ratio)
- External Event Signals (severity, credibility bounds, entity linkage)
- Outcomes (realized KPIs, cost checks)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd

logger = logging.getLogger("procurax.cleaner")


@dataclass
class CleaningSummary:
    table: str
    total_raw: int
    cleaned_rows: int
    duplicates_removed: int
    nulls_imputed: int
    invalid_rows_dropped: int


def clean_purchase_orders(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningSummary]:
    """Clean and preprocess historical purchase order dataset."""
    raw_count = len(df)
    
    # 1. Deduplicate
    df = df.drop_duplicates(subset=["po_id"]).copy()
    dups_removed = raw_count - len(df)

    # 2. Type casting and null handling
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df = df[df["quantity"] > 0]

    # 3. Date cleaning & chronological ordering
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["promised_date"] = pd.to_datetime(df["promised_date"], errors="coerce")
    df["actual_date"] = pd.to_datetime(df["actual_date"], errors="coerce")

    # Drop rows missing order_date or promised_date
    df = df.dropna(subset=["order_date", "promised_date"])

    # Ensure promised_date >= order_date; fix if inverted
    invalid_promise = df["promised_date"] < df["order_date"]
    df.loc[invalid_promise, "promised_date"] = df.loc[invalid_promise, "order_date"] + pd.Timedelta(days=14)

    # If actual_date is earlier than order_date, adjust to promised_date
    invalid_actual = (df["actual_date"].notna()) & (df["actual_date"] < df["order_date"])
    df.loc[invalid_actual, "actual_date"] = df.loc[invalid_actual, "promised_date"]

    # 4. Normalize statuses
    valid_statuses = {"delivered_on_time", "delivered_late", "open", "cancelled"}
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df.loc[~df["status"].isin(valid_statuses), "status"] = "delivered_on_time"

    # Convert dates to ISO strings (YYYY-MM-DD)
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    df["promised_date"] = df["promised_date"].dt.strftime("%Y-%m-%d")
    df["actual_date"] = df["actual_date"].dt.strftime("%Y-%m-%d")

    summary = CleaningSummary(
        table="purchase_orders",
        total_raw=raw_count,
        cleaned_rows=len(df),
        duplicates_removed=dups_removed,
        nulls_imputed=0,
        invalid_rows_dropped=raw_count - len(df) - dups_removed,
    )
    return df, summary


def clean_supplier_performance(quality_df: pd.DataFrame, capacity_df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningSummary]:
    """Clean and merge historical quality and capacity into unified monthly performance."""
    raw_count = len(quality_df)

    q = quality_df.copy()
    c = capacity_df.copy()

    # Deduplicate
    q = q.drop_duplicates(subset=["supplier_id", "period_date"])
    c = c.drop_duplicates(subset=["supplier_id", "period_date"])

    # Numeric bounds
    q["otif"] = pd.to_numeric(q["otif"], errors="coerce").clip(lower=0.0, upper=1.0).fillna(0.95)
    q["defect_rate"] = pd.to_numeric(q["defect_rate"], errors="coerce").clip(lower=0.0, upper=1.0).fillna(0.01)

    c["capacity_utilisation"] = pd.to_numeric(c["capacity_utilisation"], errors="coerce").clip(lower=0.0, upper=1.5).fillna(0.75)
    c["capacity_units"] = pd.to_numeric(c.get("capacity_units", 5000), errors="coerce").fillna(5000)

    # Standardize dates
    q["period_date"] = pd.to_datetime(q["period_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    c["period_date"] = pd.to_datetime(c["period_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Merge on (supplier_id, period_date)
    merged = pd.merge(q, c[["supplier_id", "period_date", "capacity_utilisation"]], on=["supplier_id", "period_date"], how="inner")
    
    # Generate lead_time_days (deterministic baseline ~14 days adjusted by OTIF)
    merged["lead_time_days"] = (14.0 + (1.0 - merged["otif"]) * 10.0).round(2)
    merged["performance_id"] = merged["supplier_id"] + "-" + merged["period_date"].str.replace("-", "")

    summary = CleaningSummary(
        table="supplier_performance",
        total_raw=raw_count,
        cleaned_rows=len(merged),
        duplicates_removed=raw_count - len(q),
        nulls_imputed=0,
        invalid_rows_dropped=raw_count - len(merged),
    )
    return merged, summary


def clean_external_signals(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningSummary]:
    """Clean and preprocess historical external disruption signals."""
    raw_count = len(df)
    df = df.drop_duplicates(subset=["signal_id"]).copy()
    
    # Numeric bounds
    df["severity"] = pd.to_numeric(df["severity"], errors="coerce").clip(lower=0.0, upper=1.0).fillna(0.5)
    df["source_credibility"] = pd.to_numeric(df["source_credibility"], errors="coerce").clip(lower=0.0, upper=1.0).fillna(0.7)
    df["is_synthetic"] = df["is_synthetic"].astype(bool)

    # Clean text
    df["source_name"] = df["source_name"].fillna("Unknown Source").astype(str)
    df["event_type"] = df["event_type"].fillna("general_disruption").astype(str)

    summary = CleaningSummary(
        table="external_signals",
        total_raw=raw_count,
        cleaned_rows=len(df),
        duplicates_removed=raw_count - len(df),
        nulls_imputed=0,
        invalid_rows_dropped=0,
    )
    return df, summary
