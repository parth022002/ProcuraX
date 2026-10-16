"""Tests for Sprint 0/1 Data Foundation, Reproducibility, Quality, and Leakage Guards."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from app.services.data_quality import (
    ALLOWED_PROVENANCE,
    assert_temporal_outcome_guard,
    assert_training_leakage_guard,
    validate_dataset,
    verify_checksums,
)
from scripts.generate_synthetic_data import generate

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "generated"


def test_synthetic_data_reproducibility():
    """Generating dataset twice with the same seed, as-of, and scale must produce identical hashes."""
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1)
        dir2 = Path(tmp2)
        generate(dir1, seed=42, as_of="2026-09-30", scale="small")
        generate(dir2, seed=42, as_of="2026-09-30", scale="small")

        checksums1 = (dir1 / "checksums.txt").read_text(encoding="utf-8")
        checksums2 = (dir2 / "checksums.txt").read_text(encoding="utf-8")
        assert checksums1 == checksums2, "Checksums for identical seed must match byte-for-byte"

        ok1, issues1 = verify_checksums(dir1)
        ok2, issues2 = verify_checksums(dir2)
        assert ok1 and not issues1
        assert ok2 and not issues2


def test_data_quality_report_on_generated_data():
    """Generated dataset in data/generated must satisfy all structural and relational DQ constraints."""
    if not (DATA_DIR / "supplier.csv").exists():
        generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")

    report = validate_dataset(DATA_DIR)
    errors = [i for i in report.issues if i.severity == "ERROR"]
    assert report.is_valid, f"Data quality validation failed with errors: {[e.message for e in errors]}"
    assert report.checksum_verified, "Checksums must verify against generated CSVs"
    assert report.provenance_verified, "Metadata provenance must be valid"
    assert report.tables_checked == 8, "All 8 entity tables must be verified"
    assert report.row_counts["supplier.csv"] == 60
    assert report.row_counts["po.csv"] > 1000


def test_flagship_supplier_leakage_guard():
    """Injected degradation rows for SUP-1047 in the 90-day window must trigger an assertion if included in training."""
    if not (DATA_DIR / "quality.csv").exists():
        generate(DATA_DIR, seed=42, as_of="2026-09-30", scale="small")

    quality_df = pd.read_csv(DATA_DIR / "quality.csv")

    # Contaminated training set (contains SUP-1047 during the 90-day degradation period)
    with pytest.raises(AssertionError, match="LEAKAGE DETECTED"):
        assert_training_leakage_guard(
            quality_df,
            as_of_date="2026-09-30",
            injected_supplier_id="SUP-1047",
            holdout_days=90,
            date_column="period_date",
            supplier_column="supplier_id",
        )

    # Properly filtered training set (degradation window excluded)
    as_of = pd.Timestamp("2026-09-30").normalize()
    cutoff = as_of - pd.Timedelta(days=90)
    dates = pd.to_datetime(quality_df["period_date"])
    safe_training_df = quality_df[
        ~((quality_df["supplier_id"] == "SUP-1047") & (dates >= cutoff) & (dates <= as_of))
    ]

    # Must pass without raising
    assert_training_leakage_guard(
        safe_training_df,
        as_of_date="2026-09-30",
        injected_supplier_id="SUP-1047",
        holdout_days=90,
        date_column="period_date",
        supplier_column="supplier_id",
    )


def test_temporal_outcome_leakage_guard():
    """Prediction-time features must not contain future delivery actuals or post-event outcome columns."""
    safe_features = pd.DataFrame({
        "supplier_id": ["SUP-1001", "SUP-1047"],
        "historical_otif": [0.94, 0.91],
        "historical_defect_rate": [0.012, 0.018],
    })
    # Must pass
    assert_temporal_outcome_guard(safe_features, prediction_time="2026-07-01")

    # Contaminated feature set with actual_delivery_date
    leaked_features = safe_features.copy()
    leaked_features["actual_delivery_date"] = ["2026-07-15", "2026-07-22"]
    with pytest.raises(AssertionError, match="OUTCOME LEAKAGE DETECTED"):
        assert_temporal_outcome_guard(leaked_features, prediction_time="2026-07-01")

    # Contaminated feature set with outcome labels
    leaked_labels = safe_features.copy()
    leaked_labels["disrupted_flag"] = [0, 1]
    with pytest.raises(AssertionError, match="OUTCOME LEAKAGE DETECTED"):
        assert_temporal_outcome_guard(leaked_labels, prediction_time="2026-07-01")


def test_provenance_classes():
    """All system records and provenance metadata must belong to the approved provenance enum."""
    expected_classes = {"PUBLIC_REAL", "SYNTHETIC", "DERIVED", "ILLUSTRATIVE"}
    assert ALLOWED_PROVENANCE == expected_classes
