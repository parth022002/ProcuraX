#!/usr/bin/env python3
"""Generate reproducible, explicitly synthetic ProcuraX data.

Outputs one CSV per core entity plus checksums.txt and metadata.json. The SUP-1047
ApexDrive disruption is injected in the last 90 days of the generated history and
must remain in a held-out time window, never in training data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

GENERATOR_VERSION = "procurax-synthetic-v0.1"
DEFAULT_AS_OF = "2026-09-30"
PLANTS = ["Pune", "Chennai", "Greater Noida"]
CATEGORIES = ["Motor components", "Electronics", "Moulded parts", "Fasteners", "Packaging"]
FAMILIES = ["BLDC motor", "Control board", "Power module", "Drive assembly", "Housing"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/generated", help="Directory for generated CSVs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF, help="Frozen YYYY-MM-DD anchor date")
    parser.add_argument("--scale", choices=["small", "enterprise"], default="small")
    return parser.parse_args()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, date_format="%Y-%m-%d")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def generate(out_dir: Path, seed: int = 42, as_of: str = DEFAULT_AS_OF, scale: str = "small") -> dict[str, Path]:
    rng = np.random.default_rng(seed)
    as_of_ts = pd.Timestamp(as_of).normalize()
    if scale == "small":
        n_suppliers, n_skus, months, pos_per_month = 60, 250, 18, 320
    else:
        n_suppliers, n_skus, months, pos_per_month = 420, 1850, 36, 4800
    out_dir.mkdir(parents=True, exist_ok=True)
    history_start = (as_of_ts.replace(day=1) - pd.DateOffset(months=months - 1)).normalize()
    month_starts = pd.date_range(history_start, as_of_ts.replace(day=1), freq="MS")
    injected_start = as_of_ts - pd.Timedelta(days=90)

    # Suppliers: guarantee both IDs referenced by the flagship scenario.
    supplier_ids = [f"SUP-{1000+i}" for i in range(n_suppliers)]
    suppliers = pd.DataFrame({
        "supplier_id": supplier_ids,
        "name": [f"Supplier {i+1:03d}" for i in range(n_suppliers)],
        "category": rng.choice(CATEGORIES, n_suppliers),
        "location": rng.choice(["Maharashtra", "Tamil Nadu", "Uttar Pradesh", "Gujarat", "Karnataka"], n_suppliers),
        "strategic_flag": rng.random(n_suppliers) < 0.22,
        "annual_spend_inr": np.round(rng.lognormal(mean=16.2, sigma=1.0, size=n_suppliers), 2),
        "base_reliability": np.round(np.clip(rng.normal(0.91, 0.06, n_suppliers), 0.65, 0.995), 4),
    })
    if "SUP-1047" not in set(supplier_ids) or "SUP-1012" not in set(supplier_ids):
        raise ValueError("Selected scale must include flagship suppliers SUP-1047 and SUP-1012")
    suppliers.loc[suppliers.supplier_id == "SUP-1047", ["name", "category", "location", "strategic_flag"]] = ["ApexDrive Components", "Motor components", "Maharashtra", True]
    suppliers.loc[suppliers.supplier_id == "SUP-1012", ["name", "category", "location", "strategic_flag"]] = ["ElectroMotion Systems", "Motor components", "Gujarat", True]

    skus = pd.DataFrame({
        "sku_id": [f"SKU-{i+1:05d}" for i in range(n_skus)],
        "family": rng.choice(FAMILIES, n_skus),
        "unit_contribution_margin_inr": np.round(rng.uniform(150, 12000, n_skus), 2),
        "criticality": rng.choice([1, 2, 3, 4, 5], n_skus, p=[0.15, 0.2, 0.25, 0.25, 0.15]),
    })

    # Supplier performance time series, with the injected event only in the last 90 days.
    performance_rows = []
    capacity_rows = []
    for supplier_id in supplier_ids:
        base_rel = float(suppliers.loc[suppliers.supplier_id == supplier_id, "base_reliability"].iloc[0])
        for month in month_starts:
            period_end = min(month + pd.offsets.MonthEnd(0), as_of_ts)
            disrupted = supplier_id == "SUP-1047" and period_end >= injected_start
            otif = float(np.clip(rng.normal(base_rel, 0.035), 0.45, 0.995))
            lead = float(max(3, rng.normal(15, 4)))
            defect = float(np.clip(rng.beta(1.4, 60), 0.0001, 0.12))
            utilisation = float(np.clip(rng.normal(0.74, 0.10), 0.35, 0.99))
            if disrupted:
                otif = float(np.clip(otif - rng.uniform(0.18, 0.35), 0.30, 0.75))
                lead += float(rng.uniform(8, 18))
                defect = float(np.clip(defect + rng.uniform(0.015, 0.05), 0.01, 0.16))
                utilisation = float(np.clip(utilisation + rng.uniform(0.10, 0.22), 0.85, 0.999))
            performance_rows.append({
                "performance_id": f"PERF-{supplier_id}-{period_end:%Y%m}", "supplier_id": supplier_id,
                "period_date": period_end.date().isoformat(), "otif": round(otif, 4),
                "lead_time_days": round(lead, 2), "defect_rate": round(defect, 4),
                "capacity_utilisation": round(utilisation, 4),
            })
            capacity_rows.append({
                "capacity_id": f"CAP-{supplier_id}-{period_end:%Y%m}", "supplier_id": supplier_id,
                "period_date": period_end.date().isoformat(), "capacity_units": int(rng.integers(500, 7000)),
                "capacity_utilisation": round(utilisation, 4),
            })
    performance = pd.DataFrame(performance_rows)
    capacity = pd.DataFrame(capacity_rows)

    # Inventory by SKU and plant; intentionally generated independently of future outcomes.
    inventory_rows = []
    for _, sku in skus.iterrows():
        plant = str(rng.choice(PLANTS))
        demand = float(rng.uniform(8, 420))
        on_hand = int(max(0, rng.normal(demand * rng.uniform(2.0, 12.0), demand)))
        safety = int(max(0, demand * rng.uniform(2.0, 5.0)))
        inventory_rows.append({
            "inventory_id": f"INV-{sku.sku_id}-{plant.replace(' ', '')}", "sku_id": sku.sku_id,
            "plant": plant, "on_hand_units": on_hand, "safety_stock_units": safety,
            "average_daily_consumption": round(demand, 3),
        })
    inventory = pd.DataFrame(inventory_rows)

    # POs: generate orders in each historical month; actuals are outcome fields and must not be used
    # for features before actual delivery time. A close-of-window buffer prevents future actual dates.
    po_rows = []
    order_counter = 1
    supplier_rel = dict(zip(suppliers.supplier_id, suppliers.base_reliability))
    sku_ids = skus.sku_id.to_numpy()
    for month in month_starts:
        month_end = min(month + pd.offsets.MonthEnd(0), as_of_ts - pd.Timedelta(days=35))
        if month > month_end:
            continue
        days = max(1, (month_end - month).days + 1)
        dates = month + pd.to_timedelta(rng.integers(0, days, size=pos_per_month), unit="D")
        for order_date in dates:
            supplier_id = str(rng.choice(supplier_ids))
            sku_id = str(rng.choice(sku_ids))
            performance_match = performance[(performance.supplier_id == supplier_id) & (pd.to_datetime(performance.period_date) <= order_date)]
            base_lead = 15.0
            if not performance_match.empty:
                base_lead = float(performance_match.iloc[-1].lead_time_days)
            lead = int(max(3, round(rng.normal(base_lead, 3))))
            promised = pd.Timestamp(order_date) + pd.Timedelta(days=lead)
            reliability = float(supplier_rel[supplier_id])
            is_late = bool(rng.random() > reliability)
            lateness = int(rng.integers(1, 13)) if is_late else 0
            if supplier_id == "SUP-1047" and pd.Timestamp(order_date) >= injected_start:
                lateness += int(rng.integers(4, 16))
            actual = promised + pd.Timedelta(days=lateness)
            po_rows.append({
                "po_id": f"PO-{order_counter:07d}", "supplier_id": supplier_id, "sku_id": sku_id,
                "quantity": int(rng.integers(10, 1200)), "order_date": pd.Timestamp(order_date).date().isoformat(),
                "promised_date": promised.date().isoformat(), "actual_date": actual.date().isoformat(),
                "status": "late" if lateness > 0 else "delivered_on_time",
                "late_days": lateness,
            })
            order_counter += 1
    purchase_orders = pd.DataFrame(po_rows)

    # External event table: noise + a labelled injected SUP-1047 commodity-shortage event.
    event_rows = []
    n_noise = max(15, int(n_suppliers * 0.8))
    for i in range(n_noise):
        event_date = history_start + pd.Timedelta(days=int(rng.integers(0, max(1, (as_of_ts-history_start).days + 1))))
        supplier_id = str(rng.choice(supplier_ids))
        event_rows.append({
            "signal_id": f"SIG-{i+1:05d}", "source_name": "synthetic-public-feed",
            "source_url": "synthetic://not-a-real-source", "source_timestamp": event_date.isoformat(),
            "event_type": str(rng.choice(["port_delay", "weather", "regulatory_change", "capacity_notice", "commodity_update"])),
            "supplier_id": supplier_id, "region": str(suppliers.loc[suppliers.supplier_id == supplier_id, "location"].iloc[0]),
            "material": str(rng.choice(FAMILIES)), "severity": round(float(rng.uniform(0.15, 0.7)), 4),
            "source_credibility": round(float(rng.uniform(0.35, 0.85)), 4), "is_synthetic": True,
            "is_injected_flagship": False,
        })
    event_rows.append({
        "signal_id": "SIG-FLAGSHIP-SUP1047", "source_name": "synthetic-injected-event",
        "source_url": "synthetic://flagship-scenario", "source_timestamp": injected_start.isoformat(),
        "event_type": "raw_material_shortage", "supplier_id": "SUP-1047", "region": "Maharashtra",
        "material": "specialised magnetic material for BLDC motor", "severity": 0.94,
        "source_credibility": 0.80, "is_synthetic": True, "is_injected_flagship": True,
    })
    external_events = pd.DataFrame(event_rows)

    # Outcome table deliberately separated from feature tables and timestamped post-decision.
    outcomes = []
    for idx, supplier_id in enumerate(supplier_ids):
        decision_ts = as_of_ts - pd.Timedelta(days=int(rng.integers(15, 85)))
        observed_ts = decision_ts + pd.Timedelta(days=int(rng.integers(7, 30)))
        rel = float(supplier_rel[supplier_id])
        if supplier_id == "SUP-1047":
            rel = max(0.35, rel - 0.24)
        outcomes.append({
            "outcome_id": f"OUT-{idx+1:05d}", "supplier_id": supplier_id,
            "decision_timestamp": decision_ts.isoformat(), "observed_at": observed_ts.isoformat(),
            "action": str(rng.choice(["no_action", "supplier_shift", "expedite_inventory", "hybrid"])),
            "actual_otif": round(float(np.clip(rng.normal(rel, 0.04), 0.25, 0.999)), 4),
            "actual_service_level": round(float(np.clip(rng.normal(0.96 if supplier_id != "SUP-1047" else 0.77, 0.08), 0.3, 0.999)), 4),
            "actual_cost_inr": round(float(rng.uniform(100000, 10000000)), 2),
            "outcome_label": "disruption" if supplier_id == "SUP-1047" else ("stable" if rel >= 0.88 else "watch"),
            "is_post_decision_outcome": True,
        })
    outcome_df = pd.DataFrame(outcomes)

    frames = {
        "supplier.csv": suppliers,
        "sku.csv": skus,
        "po.csv": purchase_orders,
        "inventory.csv": inventory,
        "quality.csv": performance[["performance_id", "supplier_id", "period_date", "defect_rate", "otif"]].copy(),
        "capacity.csv": capacity,
        "external_event.csv": external_events,
        "outcome.csv": outcome_df,
    }
    paths: dict[str, Path] = {}
    for filename, frame in frames.items():
        destination = out_dir / filename
        write_csv(frame, destination)
        paths[filename] = destination

    metadata = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "as_of": as_of_ts.date().isoformat(),
        "scale": scale,
        "history_start": history_start.date().isoformat(),
        "injected_event_start": injected_start.date().isoformat(),
        "injected_supplier_id": "SUP-1047",
        "injected_event_id": "SIG-FLAGSHIP-SUP1047",
        "provenance": "SYNTHETIC",
        "synthetic_data_only": True,
        "note": "Keep injected flagship event in held-out/test period; outcomes are post-decision and must not be joined into prediction-time features.",
        "rows": {filename: int(len(frame)) for filename, frame in frames.items()},
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
    }
    metadata_path = out_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    paths["metadata.json"] = metadata_path
    checksums = [f"{sha256(path)}  {path.name}" for name, path in sorted(paths.items()) if name != "checksums.txt"]
    checksums_path = out_dir / "checksums.txt"
    checksums_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")
    paths["checksums.txt"] = checksums_path
    return paths


def main() -> None:
    args = parse_args()
    try:
        paths = generate(Path(args.out), args.seed, args.as_of, args.scale)
    except Exception as exc:
        print(f"ERROR: data generation failed: {exc}", file=sys.stderr)
        raise
    print(f"Generated synthetic ProcuraX dataset in: {Path(args.out).resolve()}")
    for name, path in sorted(paths.items()):
        print(f"  {name}: {path.stat().st_size:,} bytes")
    print("Reminder: verify time cutoffs and keep the injected SUP-1047 case out of training.")

if __name__ == "__main__":
    main()
