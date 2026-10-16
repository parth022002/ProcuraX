"""Data quality and leakage validation service for ProcuraX.

Enforces Sprint 0/1 data foundation gates:
- Entity integrity and foreign-key reconciliation
- Range, uniqueness, and temporal-ordering constraints
- Provenance tracking (PUBLIC_REAL, SYNTHETIC, DERIVED, ILLUSTRATIVE)
- Leakage guards: holding out the SUP-1047 degradation window from training
- Preventing future outcomes from contaminating historical feature rows
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

ALLOWED_PROVENANCE = {"PUBLIC_REAL", "SYNTHETIC", "DERIVED", "ILLUSTRATIVE"}
EXPECTED_TABLES = [
    "capacity.csv",
    "external_event.csv",
    "inventory.csv",
    "outcome.csv",
    "po.csv",
    "quality.csv",
    "sku.csv",
    "supplier.csv",
]


@dataclass
class ValidationIssue:
    severity: str  # "ERROR" | "WARNING"
    category: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQualityReport:
    is_valid: bool
    tables_checked: int
    row_counts: dict[str, int]
    issues: list[ValidationIssue]
    checksum_verified: bool
    provenance_verified: bool
    leakage_guards_passed: bool

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        err_count = sum(1 for i in self.issues if i.severity == "ERROR")
        warn_count = sum(1 for i in self.issues if i.severity == "WARNING")
        return (
            f"DataQualityReport: {status} (Errors: {err_count}, Warnings: {warn_count}, "
            f"Tables: {self.tables_checked}, Checksums: {self.checksum_verified}, "
            f"LeakageGuards: {self.leakage_guards_passed})"
        )


def verify_checksums(data_dir: Path) -> tuple[bool, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    checksum_file = data_dir / "checksums.txt"
    if not checksum_file.exists():
        issues.append(ValidationIssue("ERROR", "CHECKSUM", "checksums.txt not found in dataset directory"))
        return False, issues

    verified = True
    for line in checksum_file.read_text(encoding="utf-8").strip().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        expected_hash, filename = parts[0], parts[1].lstrip("*")
        file_path = data_dir / filename
        if not file_path.exists():
            issues.append(ValidationIssue("ERROR", "CHECKSUM", f"Missing file listed in checksums: {filename}"))
            verified = False
            continue

        h = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        actual_hash = h.hexdigest()
        if actual_hash != expected_hash:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    "CHECKSUM",
                    f"Checksum mismatch for {filename}: expected {expected_hash[:8]}..., got {actual_hash[:8]}...",
                )
            )
            verified = False

    return verified, issues


def validate_dataset(data_dir: Path | str) -> DataQualityReport:
    """Run comprehensive data quality checks on a ProcuraX dataset folder."""
    path = Path(data_dir)
    issues: list[ValidationIssue] = []
    row_counts: dict[str, int] = {}

    # 1. File presence
    for table_name in EXPECTED_TABLES:
        table_path = path / table_name
        if not table_path.exists():
            issues.append(ValidationIssue("ERROR", "MISSING_FILE", f"Required table file missing: {table_name}"))

    # 2. Checksum verification
    checksum_ok, checksum_issues = verify_checksums(path)
    issues.extend(checksum_issues)

    # 3. Metadata and Provenance
    meta_path = path / "metadata.json"
    provenance_ok = False
    if meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            provenance = metadata.get("provenance") or ("SYNTHETIC" if metadata.get("synthetic_data_only") else "")
            if provenance in ALLOWED_PROVENANCE:
                provenance_ok = True
            else:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "PROVENANCE",
                        f"Invalid provenance class '{provenance}'. Allowed: {sorted(ALLOWED_PROVENANCE)}",
                    )
                )
        except Exception as exc:
            issues.append(ValidationIssue("ERROR", "METADATA", f"Failed to parse metadata.json: {exc}"))
    else:
        issues.append(ValidationIssue("ERROR", "METADATA", "metadata.json not found"))

    # If any essential file missing, return early
    if any(i.category == "MISSING_FILE" for i in issues):
        return DataQualityReport(
            is_valid=False,
            tables_checked=0,
            row_counts=row_counts,
            issues=issues,
            checksum_verified=False,
            provenance_verified=False,
            leakage_guards_passed=False,
        )

    # 4. Load DataFrames
    dfs = {name: pd.read_csv(path / name) for name in EXPECTED_TABLES}
    for name, df in dfs.items():
        row_counts[name] = len(df)
        if len(df) == 0:
            issues.append(ValidationIssue("ERROR", "EMPTY_TABLE", f"Table {name} contains 0 rows"))

    # 5. Primary Key Uniqueness and Non-Null
    pk_map = {
        "supplier.csv": "supplier_id",
        "sku.csv": "sku_id",
        "po.csv": "po_id",
        "quality.csv": "performance_id" if "performance_id" in dfs["quality.csv"].columns else "quality_id",
        "capacity.csv": "capacity_id",
        "inventory.csv": "inventory_id",
        "external_event.csv": "signal_id" if "signal_id" in dfs["external_event.csv"].columns else "event_id",
        "outcome.csv": "outcome_id",
    }
    for filename, pk in pk_map.items():
        df = dfs[filename]
        if pk not in df.columns:
            issues.append(ValidationIssue("ERROR", "SCHEMA", f"PK column '{pk}' missing from {filename}"))
            continue
        null_count = int(df[pk].isna().sum())
        if null_count > 0:
            issues.append(ValidationIssue("ERROR", "NULL_PK", f"{null_count} null primary keys in {filename} ({pk})"))
        dup_count = int(df[pk].duplicated().sum())
        if dup_count > 0:
            issues.append(ValidationIssue("ERROR", "DUPLICATE_PK", f"{dup_count} duplicate primary keys in {filename} ({pk})"))

    # 6. Foreign Key Relationships
    supplier_ids = set(dfs["supplier.csv"]["supplier_id"].dropna())
    sku_ids = set(dfs["sku.csv"]["sku_id"].dropna())

    for filename, fk_col, parent_set, parent_name in [
        ("po.csv", "supplier_id", supplier_ids, "supplier"),
        ("capacity.csv", "supplier_id", supplier_ids, "supplier"),
        ("quality.csv", "supplier_id", supplier_ids, "supplier"),
        ("po.csv", "sku_id", sku_ids, "sku"),
        ("inventory.csv", "sku_id", sku_ids, "sku"),
    ]:
        df = dfs[filename]
        if fk_col in df.columns:
            invalid_fks = set(df[fk_col].dropna()) - parent_set
            if invalid_fks:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "FOREIGN_KEY",
                        f"{len(invalid_fks)} unreferenced {fk_col} values in {filename} (not in {parent_name})",
                        {"invalid_samples": list(invalid_fks)[:5]},
                    )
                )

    # 7. Value Range Constraints
    po_df = dfs["po.csv"]
    if "unit_price_inr" in po_df.columns and (po_df["unit_price_inr"] <= 0).any():
        issues.append(ValidationIssue("ERROR", "RANGE", "Negative or zero unit_price_inr found in po.csv"))
    if "quantity" in po_df.columns and (po_df["quantity"] <= 0).any():
        issues.append(ValidationIssue("ERROR", "RANGE", "Negative or zero quantity found in po.csv"))

    quality_df = dfs["quality.csv"]
    if "defect_rate" in quality_df.columns and ((quality_df["defect_rate"] < 0) | (quality_df["defect_rate"] > 1)).any():
        issues.append(ValidationIssue("ERROR", "RANGE", "defect_rate outside [0, 1] in quality.csv"))

    capacity_df = dfs["capacity.csv"]
    if "capacity_utilisation" in capacity_df.columns and (
        (capacity_df["capacity_utilisation"] < 0) | (capacity_df["capacity_utilisation"] > 1.05)
    ).any():
        issues.append(ValidationIssue("ERROR", "RANGE", "capacity_utilisation outside [0, 1.05] in capacity.csv"))

    # 8. Temporal Ordering
    if "order_date" in po_df.columns and "expected_delivery_date" in po_df.columns:
        invalid_time_order = (pd.to_datetime(po_df["order_date"]) > pd.to_datetime(po_df["expected_delivery_date"])).sum()
        if invalid_time_order > 0:
            issues.append(ValidationIssue("ERROR", "TEMPORAL", f"{invalid_time_order} POs have order_date > expected_delivery_date"))

    # 9. Flagship Injected Disruption Presence Check
    # Verify that SUP-1047 (ApexDrive Components) exists in supplier table
    if "SUP-1047" not in supplier_ids:
        issues.append(ValidationIssue("ERROR", "FLAGSHIP", "Flagship supplier SUP-1047 missing from supplier.csv"))

    error_count = sum(1 for i in issues if i.severity == "ERROR")
    is_valid = error_count == 0

    return DataQualityReport(
        is_valid=is_valid,
        tables_checked=len(EXPECTED_TABLES),
        row_counts=row_counts,
        issues=issues,
        checksum_verified=checksum_ok,
        provenance_verified=provenance_ok,
        leakage_guards_passed=is_valid,
    )


def assert_training_leakage_guard(
    training_df: pd.DataFrame,
    as_of_date: str = "2026-09-30",
    injected_supplier_id: str = "SUP-1047",
    holdout_days: int = 90,
    date_column: str = "period_date",
    supplier_column: str = "supplier_id",
) -> None:
    """Assert that injected flagship degradation records are strictly absent from training rows.

    Raises AssertionError if any record for `injected_supplier_id` falling within the
    holdout window (`as_of_date - holdout_days` to `as_of_date`) is present in `training_df`.
    """
    as_of = pd.Timestamp(as_of_date).normalize()
    cutoff = as_of - pd.Timedelta(days=holdout_days)

    if supplier_column not in training_df.columns:
        raise ValueError(f"Column '{supplier_column}' not found in training DataFrame")
    if date_column not in training_df.columns:
        raise ValueError(f"Column '{date_column}' not found in training DataFrame")

    dates = pd.to_datetime(training_df[date_column])
    flagship_mask = (training_df[supplier_column] == injected_supplier_id) & (dates >= cutoff) & (dates <= as_of)
    contaminated_count = int(flagship_mask.sum())

    if contaminated_count > 0:
        raise AssertionError(
            f"LEAKAGE DETECTED: {contaminated_count} rows of injected flagship supplier "
            f"'{injected_supplier_id}' from the held-out degradation window ({cutoff.date()} to {as_of.date()}) "
            f"were found in the training split! Flagship degradation must remain held-out for test/replay only."
        )


def assert_temporal_outcome_guard(
    features_df: pd.DataFrame,
    prediction_time: str,
    forbidden_columns: tuple[str, ...] = ("actual_delivery_date", "on_time", "delayed_days", "disrupted_flag"),
) -> None:
    """Assert that post-event delivery actuals and future outcome labels do not contaminate prediction-time features."""
    leaked_cols = [col for col in forbidden_columns if col in features_df.columns]
    if leaked_cols:
        raise AssertionError(
            f"OUTCOME LEAKAGE DETECTED: Prediction-time features as of {prediction_time} contain "
            f"future outcome fields: {leaked_cols}. Outcome metrics can only be observed after actual delivery."
        )
