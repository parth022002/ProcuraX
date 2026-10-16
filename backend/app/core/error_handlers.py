"""Standardized Operational Error Handlers for ProcuraX.

Guarantees that all API errors return structured operational error envelopes explaining:
- What happened (error, status_code)
- Why it happened (detail)
- Correlation traceability (trace_id)
- Next permitted action (next_permitted_action)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.core.logging_config import current_trace_id, generate_trace_id
from app.core.safe_requests import SSRFSecurityError

logger = logging.getLogger("procurax.error_handler")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_active_trace_id(request: Request) -> str:
    return current_trace_id.get() or request.headers.get("x-trace-id") or generate_trace_id("TRC")


def get_next_permitted_action(status_code: int, detail: str) -> str:
    """Derive governed, actionable guidance for users based on failure reason."""
    detail_lower = detail.lower()
    if status_code == 401:
        return "Authenticate via Authorization Bearer token or supply valid user role credentials."
    if status_code == 403:
        if "tenant" in detail_lower:
            return "Switch active tenant to 'ApexDrive Components' (TENANT-APEX-01) or request multi-tenant privileges."
        if "cpo" in detail_lower or "spend" in detail_lower:
            return "Escalate approval request to Chief Procurement Officer (CPO) or Category Director."
        return "Request elevated procurement governance privileges from system administrator."
    if status_code == 404:
        return "Verify target identifier against authoritative inventory and supplier registry."
    if status_code == 422:
        return "Inspect request payload schema against OpenAPI contract specification at /docs."
    if status_code == 429:
        return "Wait for Retry-After duration before retrying API operations."
    return "Contact procurement engineering support with the provided correlation trace_id."


def register_error_handlers(app: FastAPI) -> None:
    """Register uniform operational error handlers on the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        trace_id = _get_active_trace_id(request)
        next_action = get_next_permitted_action(exc.status_code, str(exc.detail))
        
        logger.warning(
            f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail} [trace_id={trace_id}]"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "trace_id": trace_id,
                "timestamp_utc": _now_utc(),
                "next_permitted_action": next_action,
            },
            headers={"X-Trace-ID": trace_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = _get_active_trace_id(request)
        errors = exc.errors()
        error_msgs = []
        for err in errors:
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Validation error")
            error_msgs.append(f"{loc}: {msg}")
        
        detail_str = "; ".join(error_msgs)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "UNPROCESSABLE_ENTITY",
                "detail": f"Schema validation failed: {detail_str}",
                "status_code": 422,
                "errors": errors,
                "trace_id": trace_id,
                "timestamp_utc": _now_utc(),
                "next_permitted_action": "Review request payload parameters against OpenAPI schema at /docs.",
            },
            headers={"X-Trace-ID": trace_id},
        )

    @app.exception_handler(SSRFSecurityError)
    async def ssrf_exception_handler(request: Request, exc: SSRFSecurityError):
        trace_id = _get_active_trace_id(request)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "SSRF_SECURITY_VIOLATION",
                "detail": str(exc),
                "status_code": 400,
                "trace_id": trace_id,
                "timestamp_utc": _now_utc(),
                "next_permitted_action": "Target URL must belong to approved external intelligence provider whitelist.",
            },
            headers={"X-Trace-ID": trace_id},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        trace_id = _get_active_trace_id(request)
        logger.error(
            f"Unhandled server error on {request.method} {request.url.path}: {exc} [trace_id={trace_id}]",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "detail": f"An unexpected system exception occurred: {str(exc)}",
                "status_code": 500,
                "trace_id": trace_id,
                "timestamp_utc": _now_utc(),
                "next_permitted_action": "Contact operations support quoting trace_id for audit diagnosis.",
            },
            headers={"X-Trace-ID": trace_id},
        )
