#!/usr/bin/env python3
"""CLI utility for ProcuraX Data Quality and Leakage Guard validation.

Usage:
    python scripts/data_quality_validator.py [--dir data/generated]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add backend to path so services can be imported
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.data_quality import validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="data/generated", help="Dataset directory to validate")
    args = parser.parse_args()

    data_dir = ROOT / args.dir
    print(f"Validating ProcuraX dataset in: {data_dir}")
    report = validate_dataset(data_dir)

    print("\n--- Validation Results ---")
    print(f"Tables checked: {report.tables_checked}")
    for tbl, count in sorted(report.row_counts.items()):
        print(f"  {tbl:<20} : {count:>6} rows")

    print(f"\nChecksum verification : {'PASS' if report.checksum_verified else 'FAIL'}")
    print(f"Provenance tracking   : {'PASS' if report.provenance_verified else 'FAIL'}")
    print(f"Leakage guards        : {'PASS' if report.leakage_guards_passed else 'FAIL'}")

    if report.issues:
        print("\n--- Issues Detected ---")
        for issue in report.issues:
            prefix = "[ERROR]" if issue.severity == "ERROR" else "[WARN]"
            print(f"{prefix} ({issue.category}) {issue.message}")

    print(f"\nFinal Status: {'PASS' if report.is_valid else 'FAIL'}")
    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
