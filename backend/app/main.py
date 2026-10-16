import sys
from pathlib import Path

# Ensure backend root is on sys.path regardless of execution working directory
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging_config import setup_structured_logging, TraceMiddleware
from app.core.error_handlers import register_error_handlers

# 1. Initialize Structured JSON Logging
setup_structured_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "ProcuraX Governed Disruption Intelligence API. Business routes adhere to Section 17/18 "
        "governance, RBAC spend authorization, proposal-only action packets, and tenant isolation."
    ),
)

# 2. Distributed Tracing Middleware (Injects X-Trace-ID & X-Request-ID)
app.add_middleware(TraceMiddleware)

# 3. Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# 4. CORS Middleware
allowed_origins = [o.strip() for o in settings.frontend_origin.split(",") if o.strip()]
for default_origin in ["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"]:
    if default_origin not in allowed_origins:
        allowed_origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?:\/\/.*(\.vercel\.app|\.onrender\.com|\.railway\.app)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID", "X-Trace-ID", "X-User-Role", "X-User-ID", "X-Tenant-ID"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce defense-in-depth HTTP security headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# 5. Register Standardized Operational Error Handlers
register_error_handlers(app)

app.include_router(api_router, prefix=settings.api_v1_prefix)


def custom_openapi():
    """Declare explicit security schemes and metadata in OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "ProcuraX Governed Disruption Intelligence API. Business routes adhere to Section 17/18 "
            "governance, RBAC spend authorization, proposal-only action packets, and tenant isolation."
        ),
        routes=app.routes,
    )
    if "components" not in schema:
        schema["components"] = {}
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Bearer token or deterministic test token (e.g., 'Bearer px_USR-CPO-01_CPO_...')",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service communication.",
        },
    }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "operational",
        "implementation_status": "production_candidate",
        "modules": {
            "signal_intelligence": "active",
            "risk_assessment": "active",
            "impact_engine": "active",
            "scenario_solver": "active",
            "rag_copilot": "active",
            "governed_case_orchestrator": "active",
            "approval_workbench": "active",
            "outcome_telemetry": "active",
        },
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
