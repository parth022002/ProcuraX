from fastapi import APIRouter
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Process-level health check."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
        implementation_status="scaffold",
    )


@router.get("/health/database")
def database_health_check():
    """Verify live connectivity and latency to Neon Lakebase Postgres."""
    from app.db.session import check_db_health
    return check_db_health()

