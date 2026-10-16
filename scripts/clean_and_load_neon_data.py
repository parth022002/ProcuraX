"""Preprocess, clean, and batch-load all past data into Neon Lakebase Postgres."""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.data_processing.cleaner import (
    clean_external_signals,
    clean_purchase_orders,
    clean_supplier_performance,
)

DATA_DIR = ROOT / "data" / "generated"


def get_db_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    raise ValueError("DATABASE_URL is not configured in environment or .env file.")


def run_pipeline():
    start_time = time.time()
    db_url = get_db_url()
    masked_url = re.sub(r":([^@]+)@", ":****@", db_url)
    print("=" * 80)
    print("PROCURAX HISTORICAL DATA CLEANING & NEON POSTGRES LOADER")
    print(f"Target Database: {masked_url}")
    print("=" * 80)

    # 1. Connect to Neon
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    print("[OK] Connected to Neon Lakebase Postgres.")

    # 2. Seed Clean Suppliers
    print("\n--- 1. Suppliers ---")
    suppliers_df = pd.read_csv(DATA_DIR / "supplier.csv")
    suppliers_rows = [
        (
            r["supplier_id"],
            r["name"],
            r["category"],
            r["location"],
            bool(r["strategic_flag"]),
            float(r["annual_spend_inr"]),
            float(r["base_reliability"]),
        )
        for _, r in suppliers_df.iterrows()
    ]
    cur.execute("SELECT count(*) FROM suppliers;")
    execute_batch(
        cur,
        """
        INSERT INTO suppliers (supplier_id, name, category, location, strategic_flag, annual_spend_inr, base_reliability)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (supplier_id) DO UPDATE SET
            name = EXCLUDED.name,
            annual_spend_inr = EXCLUDED.annual_spend_inr,
            base_reliability = EXCLUDED.base_reliability;
        """,
        suppliers_rows,
    )
    print(f"[OK] Seeded {len(suppliers_rows)} suppliers.")

    # 3. Seed Clean SKUs
    print("\n--- 2. SKUs ---")
    skus_df = pd.read_csv(DATA_DIR / "sku.csv")
    sku_rows = [
        (
            r["sku_id"],
            r["family"],
            float(r["unit_contribution_margin_inr"]),
            int(r["criticality"]),
        )
        for _, r in skus_df.iterrows()
    ]
    execute_batch(
        cur,
        """
        INSERT INTO skus (sku_id, family, unit_contribution_margin_inr, criticality)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (sku_id) DO UPDATE SET
            unit_contribution_margin_inr = EXCLUDED.unit_contribution_margin_inr,
            criticality = EXCLUDED.criticality;
        """,
        sku_rows,
    )
    print(f"[OK] Seeded {len(sku_rows)} SKUs.")

    # 4. Seed Clean Inventory
    print("\n--- 3. Inventory Snapshots ---")
    inv_df = pd.read_csv(DATA_DIR / "inventory.csv")
    inv_rows = [
        (
            r["inventory_id"],
            r["sku_id"],
            r["plant"],
            int(r["on_hand_units"]),
            int(r["safety_stock_units"]),
            float(r["average_daily_consumption"]),
        )
        for _, r in inv_df.iterrows()
    ]
    execute_batch(
        cur,
        """
        INSERT INTO inventory (inventory_id, sku_id, plant, on_hand_units, safety_stock_units, average_daily_consumption)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (inventory_id) DO UPDATE SET
            on_hand_units = EXCLUDED.on_hand_units,
            safety_stock_units = EXCLUDED.safety_stock_units,
            average_daily_consumption = EXCLUDED.average_daily_consumption;
        """,
        inv_rows,
    )
    print(f"[OK] Seeded {len(inv_rows)} inventory records.")

    # 5. Clean & Load Past Purchase Orders
    print("\n--- 4. Historical Purchase Orders (Cleaning & Batch Load) ---")
    raw_po_df = pd.read_csv(DATA_DIR / "po.csv")
    clean_po_df, po_summary = clean_purchase_orders(raw_po_df)
    print(f"   * Raw POs: {po_summary.total_raw}")
    print(f"   * Cleaned POs: {po_summary.cleaned_rows} (Duplicates removed: {po_summary.duplicates_removed})")

    po_rows = [
        (
            r["po_id"],
            r["supplier_id"],
            r["sku_id"],
            int(r["quantity"]),
            r["order_date"],
            r["promised_date"],
            r["actual_date"] if pd.notna(r["actual_date"]) else None,
            r["status"],
        )
        for _, r in clean_po_df.iterrows()
    ]
    execute_batch(
        cur,
        """
        INSERT INTO purchase_orders (po_id, supplier_id, sku_id, quantity, order_date, promised_date, actual_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (po_id) DO UPDATE SET
            status = EXCLUDED.status,
            actual_date = EXCLUDED.actual_date;
        """,
        po_rows,
        page_size=1000,
    )
    print(f"[OK] Seeded {len(po_rows):,} purchase orders into Neon DB.")

    # 6. Clean & Load Past Supplier Performance (Quality + Capacity)
    print("\n--- 5. Historical Supplier Performance (OTIF, Defects, Capacity) ---")
    raw_quality_df = pd.read_csv(DATA_DIR / "quality.csv")
    raw_capacity_df = pd.read_csv(DATA_DIR / "capacity.csv")
    clean_perf_df, perf_summary = clean_supplier_performance(raw_quality_df, raw_capacity_df)
    print(f"   * Raw Quality: {len(raw_quality_df)} | Raw Capacity: {len(raw_capacity_df)}")
    print(f"   * Unified Monthly Records: {perf_summary.cleaned_rows}")

    perf_rows = [
        (
            r["performance_id"],
            r["supplier_id"],
            r["period_date"],
            float(r["otif"]),
            float(r["lead_time_days"]),
            float(r["defect_rate"]),
            float(r["capacity_utilisation"]),
        )
        for _, r in clean_perf_df.iterrows()
    ]
    execute_batch(
        cur,
        """
        INSERT INTO supplier_performance (performance_id, supplier_id, period_date, otif, lead_time_days, defect_rate, capacity_utilisation)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (supplier_id, period_date) DO UPDATE SET
            otif = EXCLUDED.otif,
            defect_rate = EXCLUDED.defect_rate,
            capacity_utilisation = EXCLUDED.capacity_utilisation;
        """,
        perf_rows,
        page_size=500,
    )
    print(f"[OK] Seeded {len(perf_rows):,} monthly performance records into Neon DB.")

    # 7. Clean & Load Historical External Signals
    print("\n--- 6. Historical Disruption Signals ---")
    raw_signals_df = pd.read_csv(DATA_DIR / "external_event.csv")
    clean_signals_df, sig_summary = clean_external_signals(raw_signals_df)
    sig_rows = [
        (
            r["signal_id"],
            r["source_name"],
            r["source_url"],
            r["source_timestamp"],
            r["event_type"],
            r["supplier_id"],
            r["region"],
            r["material"],
            float(r["severity"]),
            float(r["source_credibility"]),
            bool(r["is_synthetic"]),
        )
        for _, r in clean_signals_df.iterrows()
    ]
    execute_batch(
        cur,
        """
        INSERT INTO external_signals (signal_id, source_name, source_url, source_timestamp, event_type, supplier_id, region, material, severity, source_credibility, is_synthetic)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (signal_id) DO UPDATE SET
            severity = EXCLUDED.severity,
            source_credibility = EXCLUDED.source_credibility;
        """,
        sig_rows,
    )
    print(f"[OK] Seeded {len(sig_rows)} historical disruption signals.")

    # Final Neon DB Counts Verification
    cur.execute("SELECT count(*) FROM suppliers;")
    c_supp = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM skus;")
    c_skus = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM inventory;")
    c_inv = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM purchase_orders;")
    c_po = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM supplier_performance;")
    c_perf = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM external_signals;")
    c_sig = cur.fetchone()[0]

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print("NEON LAKEBASE POSTGRES HISTORICAL STORE VERIFIED")
    print("=" * 80)
    print(f"Suppliers              : {c_supp:,} records")
    print(f"SKUs                   : {c_skus:,} records")
    print(f"Inventory Snapshots    : {c_inv:,} records")
    print(f"Historical POs         : {c_po:,} records")
    print(f"Monthly Performance    : {c_perf:,} records")
    print(f"External Signals       : {c_sig:,} records")
    print(f"Total Database Ingestion Time: {elapsed:.2f}s")
    print("=" * 80)

    cur.close()
    conn.close()


if __name__ == "__main__":
    run_pipeline()
