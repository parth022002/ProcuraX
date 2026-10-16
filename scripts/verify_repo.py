"""Small sanity check for required starter files; does not validate feature completion."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "PROJECT.md", "AGENTS.md", "README.md", ".env.example",
    "docs/REQUIREMENTS.md", "docs/ARCHITECTURE.md", "docs/IMPLEMENTATION_PLAN.md",
    "backend/app/main.py", "frontend/package.json", "scripts/generate_synthetic_data.py",
]
missing = [item for item in REQUIRED if not (ROOT / item).exists()]
if missing:
    raise SystemExit("Missing starter files:\n- " + "\n- ".join(missing))
print(f"PASS: all {len(REQUIRED)} required starter files exist.")
