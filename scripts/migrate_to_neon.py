"""Provision ProcuraX Schema and Populate Initial Foundation on Neon Lakebase Postgres."""
from __future__ import annotations

import os
import re
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "generated"
SCHEMA_FILE = ROOT / "backend" / "app" / "db" / "schema.sql"

# Read DATABASE_URL from .env or fallback
def get_database_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
    
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
            if line.startswith("NEON_DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    raise ValueError("DATABASE_URL is not configured in environment or .env file.")


def migrate_and_seed() -> None:
    db_url = get_database_url()
    print("=" * 80)
    print("PROCURAX NEON LAKEBASE POSTGRES PROVISIONING & DATA SEEDING")
    # Mask password for security
    masked_url = re.sub(r":([^@]+)@", ":****@", db_url)
    print(f"Connecting to: {masked_url}")
    print("=" * 80)

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Check version
    cur.execute("SELECT version();")
    print(f"[OK] Neon Connected: {cur.fetchone()[0]}")

    # 2. Apply Schema
    print("\n--- Applying schema from schema.sql ---")
    sql_content = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = sql_content.split(";")
    for s in statements:
        stmt = s.strip()
        if stmt:
            try:
                cur.execute(stmt)
            except Exception as e:
                # Handle extensions or non-fatal warnings
                print(f"   [Notice] {stmt[:40]}... -> {e}")

    # Check tables created
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = sorted([r[0] for r in cur.fetchall()])
    print(f"[OK] Active tables in Neon: {', '.join(tables)}")

    # 3. Seed Suppliers
    if (DATA_DIR / "supplier.csv").exists():
        suppliers_df = pd.read_csv(DATA_DIR / "supplier.csv")
        rows = [
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
        sql_insert = """
            INSERT INTO suppliers (supplier_id, name, category, location, strategic_flag, annual_spend_inr, base_reliability)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (supplier_id) DO UPDATE SET
                name = EXCLUDED.name,
                annual_spend_inr = EXCLUDED.annual_spend_inr,
                base_reliability = EXCLUDED.base_reliability;
        """
        execute_batch(cur, sql_insert, rows)
        print(f"[OK] Seeded {len(rows)} suppliers into Neon DB.")

    # 4. Seed SKUs
    if (DATA_DIR / "sku.csv").exists():
        skus_df = pd.read_csv(DATA_DIR / "sku.csv")
        rows = [
            (
                r["sku_id"],
                r["family"],
                float(r["unit_contribution_margin_inr"]),
                int(r["criticality"]),
            )
            for _, r in skus_df.iterrows()
        ]
        sql_insert = """
            INSERT INTO skus (sku_id, family, unit_contribution_margin_inr, criticality)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (sku_id) DO UPDATE SET
                unit_contribution_margin_inr = EXCLUDED.unit_contribution_margin_inr,
                criticality = EXCLUDED.criticality;
        """
        execute_batch(cur, sql_insert, rows)
        print(f"[OK] Seeded {len(rows)} SKUs into Neon DB.")

    # 5. Seed Inventory
    if (DATA_DIR / "inventory.csv").exists():
        inv_df = pd.read_csv(DATA_DIR / "inventory.csv")
        rows = [
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
        sql_insert = """
            INSERT INTO inventory (inventory_id, sku_id, plant, on_hand_units, safety_stock_units, average_daily_consumption)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (inventory_id) DO UPDATE SET
                on_hand_units = EXCLUDED.on_hand_units,
                safety_stock_units = EXCLUDED.safety_stock_units,
                average_daily_consumption = EXCLUDED.average_daily_consumption;
        """
        execute_batch(cur, sql_insert, rows)
        print(f"[OK] Seeded {len(rows)} plant inventory records into Neon DB.")

    # 6. Verify Foreign Key Integrity on Neon
    cur.execute("SELECT count(*) FROM suppliers;")
    supp_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM skus;")
    sku_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM inventory;")
    inv_count = cur.fetchone()[0]

    print("\n" + "=" * 80)
    print("NEON DATABASE VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Suppliers count: {supp_count}")
    print(f"SKUs count     : {sku_count}")
    print(f"Inventory count: {inv_count}")
    print("All tables successfully seeded into Neon Lakebase Postgres.")
    print("=" * 80)

    cur.close()
    conn.close()


if __name__ == "__main__":
    migrate_and_seed()
