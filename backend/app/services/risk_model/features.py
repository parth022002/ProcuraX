"""Feature engineering pipeline for ProcuraX supplier risk prediction.

Extracts leakage-free historical features as of a frozen prediction cutoff timestamp.
Strictly excludes post-cutoff actuals and enforces temporal holdouts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_NAMES = [
    "otif_30d",
    "otif_90d",
    "otif_trend",
    "lead_time_mean_30d",
    "lead_time_trend",
    "defect_rate_30d",
    "defect_rate_trend",
    "capacity_utilisation_30d",
    "capacity_headroom",
    "strategic_flag",
    "annual_spend_log",
    "recent_signal_severity",
    "recent_signal_confidence",
]


@dataclass
class SupplierFeatureVector:
    supplier_id: str
    as_of_date: str
    features: dict[str, float]


def compute_supplier_features(
    supplier_id: str,
    as_of: pd.Timestamp,
    suppliers_df: pd.DataFrame,
    performance_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
    signals_df: pd.DataFrame | None = None,
) -> dict[str, float]:
    """Calculate leakage-free feature vector for one supplier as of a given timestamp."""
    # 1. Supplier static metadata
    sup_row = suppliers_df[suppliers_df["supplier_id"] == supplier_id]
    if sup_row.empty:
        raise ValueError(f"Supplier '{supplier_id}' not found in supplier table")

    strategic = 1.0 if bool(sup_row["strategic_flag"].iloc[0]) else 0.0
    spend = float(sup_row["annual_spend_inr"].iloc[0])
    spend_log = float(np.log1p(spend))
    base_rel = float(sup_row["base_reliability"].iloc[0])

    # 2. Historical performance strictly <= as_of
    perf = performance_df[
        (performance_df["supplier_id"] == supplier_id)
        & (pd.to_datetime(performance_df["period_date"]) <= as_of)
    ].copy()

    cutoff_30d = as_of - pd.Timedelta(days=35)
    cutoff_90d = as_of - pd.Timedelta(days=95)

    if not perf.empty:
        perf["dt"] = pd.to_datetime(perf["period_date"])
        perf_30d = perf[perf["dt"] >= cutoff_30d]
        perf_90d = perf[perf["dt"] >= cutoff_90d]

        otif_30d = float(perf_30d["otif"].mean()) if not perf_30d.empty else base_rel
        otif_90d = float(perf_90d["otif"].mean()) if not perf_90d.empty else base_rel
        otif_trend = float(otif_30d - otif_90d)

        if "lead_time_days" in perf.columns:
            lead_30d = float(perf_30d["lead_time_days"].mean()) if not perf_30d.empty else 15.0
            lead_90d = float(perf_90d["lead_time_days"].mean()) if not perf_90d.empty else 15.0
            lead_trend = float(lead_30d - lead_90d)
        else:
            lead_30d, lead_trend = 15.0, 0.0

        defect_30d = float(perf_30d["defect_rate"].mean()) if not perf_30d.empty else 0.02
        defect_90d = float(perf_90d["defect_rate"].mean()) if not perf_90d.empty else 0.02
        defect_trend = float(defect_30d - defect_90d)
    else:
        otif_30d, otif_90d, otif_trend = base_rel, base_rel, 0.0
        lead_30d, lead_trend = 15.0, 0.0
        defect_30d, defect_trend = 0.02, 0.0

    # 3. Capacity strictly <= as_of
    cap = capacity_df[
        (capacity_df["supplier_id"] == supplier_id)
        & (pd.to_datetime(capacity_df["period_date"]) <= as_of)
    ].copy()

    if not cap.empty:
        cap["dt"] = pd.to_datetime(cap["period_date"])
        recent_cap = cap.sort_values("dt").iloc[-1]
        cap_util = float(recent_cap["capacity_utilisation"])
        headroom = float(max(0.0, 1.0 - cap_util))
    else:
        cap_util = 0.75
        headroom = 0.25

    # 4. External Signals strictly <= as_of
    sig_sev, sig_conf = 0.0, 0.0
    if signals_df is not None and not signals_df.empty:
        sig = signals_df[
            (signals_df["supplier_id"] == supplier_id)
            & (pd.to_datetime(signals_df["source_timestamp"]) <= as_of)
            & (pd.to_datetime(signals_df["source_timestamp"]) >= cutoff_30d)
        ]
        if not sig.empty:
            sig_sev = float(sig["severity"].max())
            # Confidence = credibility * recency * 1.0 (relevance)
            sig_conf = float(sig["source_credibility"].mean())

    return {
        "otif_30d": round(otif_30d, 4),
        "otif_90d": round(otif_90d, 4),
        "otif_trend": round(otif_trend, 4),
        "lead_time_mean_30d": round(lead_30d, 2),
        "lead_time_trend": round(lead_trend, 2),
        "defect_rate_30d": round(defect_30d, 4),
        "defect_rate_trend": round(defect_trend, 4),
        "capacity_utilisation_30d": round(cap_util, 4),
        "capacity_headroom": round(headroom, 4),
        "strategic_flag": strategic,
        "annual_spend_log": round(spend_log, 3),
        "recent_signal_severity": round(sig_sev, 2),
        "recent_signal_confidence": round(sig_conf, 3),
    }


def build_dataset_slices(
    data_dir: Path | str,
    as_of_date: str = "2026-09-30",
    holdout_days: int = 90,
    train_end_date: str = "2026-06-30",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build time-aware train and test dataset slices from generated CSVs.

    Strictly quarantines the SUP-1047 degradation window from the training slice.
    Returns (train_df, test_df) where each DataFrame includes features + 'disrupted' target.
    """
    path = Path(data_dir)
    suppliers = pd.read_csv(path / "supplier.csv")
    quality = pd.read_csv(path / "quality.csv")
    capacity = pd.read_csv(path / "capacity.csv")
    events = pd.read_csv(path / "external_event.csv")

    as_of = pd.Timestamp(as_of_date).normalize()
    train_end = pd.Timestamp(train_end_date).normalize()
    cutoff_holdout = as_of - pd.Timedelta(days=holdout_days)

    quality["period_dt"] = pd.to_datetime(quality["period_date"])
    unique_periods = sorted(quality["period_dt"].unique())

    records = []
    supplier_ids = suppliers["supplier_id"].tolist()

    for period in unique_periods:
        # Check target: in the next forward period, did this supplier experience disruption?
        # Target = 1 if forward OTIF < 0.80 or forward defect_rate > 0.05 or capacity > 0.95
        forward_dt = period + pd.DateOffset(months=1)

        for sup_id in supplier_ids:
            # Features as of 'period'
            feat = compute_supplier_features(
                sup_id, period, suppliers, quality, capacity, events
            )

            # Look up forward performance for target label
            forward_perf = quality[
                (quality["supplier_id"] == sup_id)
                & (quality["period_dt"] > period)
                & (quality["period_dt"] <= forward_dt + pd.Timedelta(days=5))
            ]

            if not forward_perf.empty:
                f_otif = forward_perf["otif"].mean()
                f_defect = forward_perf["defect_rate"].mean()
                is_disrupted = int(f_otif < 0.80 or f_defect > 0.045)
            else:
                is_disrupted = 0

            feat["supplier_id"] = sup_id
            feat["period_date"] = period.strftime("%Y-%m-%d")
            feat["disrupted"] = is_disrupted
            records.append(feat)

    all_df = pd.DataFrame(records)
    all_df["period_dt"] = pd.to_datetime(all_df["period_date"])

    # Temporal split:
    # Train slice: strictly on or before train_end_date AND never contains SUP-1047 in degradation window
    train_mask = (all_df["period_dt"] <= train_end) & ~(
        (all_df["supplier_id"] == "SUP-1047") & (all_df["period_dt"] >= cutoff_holdout)
    )
    # Test slice: periods after train_end up to as_of (contains the held-out flagship replay case)
    test_mask = all_df["period_dt"] > train_end

    train_df = all_df[train_mask].drop(columns=["period_dt"]).copy()
    test_df = all_df[test_mask].drop(columns=["period_dt"]).copy()

    return train_df, test_df
