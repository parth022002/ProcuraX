import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
_backend_services = _repo_root / "backend" / "app" / "services"

if _backend_services.exists() and str(_backend_services) not in __path__:
    __path__.append(str(_backend_services))
