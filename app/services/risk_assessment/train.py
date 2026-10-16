"""Render build step compatibility entry point for risk assessment model training."""
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
_backend = _repo_root / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
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
