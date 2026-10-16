"""Structured JSON Logging and Distributed Tracing Infrastructure.

Formats all application logs into machine-readable JSON records including:
- timestamp_iso
- log_level
- logger_name
- trace_id
- request_id
- message
- path / method / status_code / latency_ms
"""
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for request-scoped correlation tracing
current_trace_id: ContextVar[str] = ContextVar("current_trace_id", default="")
current_request_id: ContextVar[str] = ContextVar("current_request_id", default="")


def generate_trace_id(prefix: str = "TRC") -> str:
    """Generate a high-entropy, human-readable correlation trace identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


class StructuredJsonFormatter(logging.Formatter):
    """Custom logging Formatter that outputs structured JSON for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": current_trace_id.get() or getattr(record, "trace_id", None),
            "request_id": current_request_id.get() or getattr(record, "request_id", None),
        }

        # Include exception details if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if provided
        for key, val in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            } and not key.startswith("_"):
                log_record[key] = val

        return json.dumps(log_record)


def setup_structured_logging(log_level: str = "INFO") -> None:
    """Initialize root logger with structured JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Replace handlers with structured stream handler
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)


class TraceMiddleware(BaseHTTPMiddleware):
    """Middleware extracting or injecting trace_id and logging HTTP request lifecycles."""

    async def dispatch(self, request: Request, call_next):
        # Extract or generate trace_id and request_id
        trace_id = request.headers.get("x-trace-id") or generate_trace_id("TRC")
        request_id = request.headers.get("x-request-id") or generate_trace_id("REQ")

        current_trace_id.set(trace_id)
        current_request_id.set(request_id)

        start_time = time.time()
        path = request.url.path
        method = request.method

        # Execute downstream handlers
        try:
            response: Response = await call_next(request)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Attach tracing headers to response
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Request-ID"] = request_id

            return response
        except Exception as exc:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            logging.getLogger("procurax.request").error(
                f"Unhandled exception on {method} {path}: {exc}",
                extra={"trace_id": trace_id, "request_id": request_id, "latency_ms": latency_ms},
            )
            raise
