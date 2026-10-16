import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_backend = _repo_root / "backend"
_backend_app = _backend / "app"

if _backend_app.exists() and str(_backend_app) not in __path__:
    __path__.append(str(_backend_app))

if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
