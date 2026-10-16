"""Render build step compatibility entry point for risk assessment model training."""
import sys
from pathlib import Path

# Dynamically discover repository root by looking for root containing both 'backend' and 'frontend'
_curr = Path(__file__).resolve()
_repo_root = None
for p in [_curr] + list(_curr.parents):
    if (p / "backend").exists() and (p / "frontend").exists():
        _repo_root = p
        break
if _repo_root is None:
    _repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent

_backend_root = _repo_root / "backend"
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.services.risk_model.model import train_and_register_baseline

def main():
    data_dir = _repo_root / "data" / "generated"
    models_dir = _repo_root / "models" / "registry"
    data_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"Training baseline risk model from {data_dir} to {models_dir}...")
    train_and_register_baseline(data_dir=data_dir, output_model_dir=models_dir)
    print("[SUCCESS] Model trained and registered successfully.")

if __name__ == "__main__":
    main()
