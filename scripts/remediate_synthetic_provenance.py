import sys
from pathlib import Path
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.db.session import get_db_connection

def clean_synthetic_records():
    try:
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE external_signals 
                SET is_synthetic = TRUE, 
                    provenance = '{"provenance_class": "SYNTHETIC", "scenario_disclaimer": "Synthetic demonstration scenario for PoC decision replay; not a real-world external event."}'
                WHERE signal_id = 'SIG-FLAGSHIP-SUP1047' 
                   OR source_name = 'synthetic-injected-event'
                   OR canonical_url LIKE 'synthetic://%';
            """)
            print(f"[SUCCESS] Updated {cur.rowcount} synthetic signal rows in Neon database.")
        conn.close()
    except Exception as exc:
        print(f"[WARNING] Database update skipped (offline or unavailable): {exc}")

if __name__ == "__main__":
    clean_synthetic_records()
