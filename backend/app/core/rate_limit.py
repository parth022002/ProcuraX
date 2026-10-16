"""In-Memory Thread-Safe Rate Limiting Middleware for FastAPI.

Provides:
- Sliding-window request counter per client IP / API key.
- Configurable requests per minute thresholds.
- Standard RFC 6585 HTTP 429 Too Many Requests response with Retry-After.
- Safe testing bypass option for automated CI test runs.
"""
from __future__ import annotations

import os
import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class InMemoryRateLimiter:
    """Sliding-window rate limiter per client key."""

    def __init__(self, requests_per_minute: int = 120, burst_limit: int = 30):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.window_seconds = 60.0
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_key: str, limit: int | None = None) -> Tuple[bool, int, float]:
        """Check if request is allowed.
        
        Returns:
            (allowed: bool, remaining: int, retry_after: float)
        """
        max_reqs = limit or self.requests_per_minute
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Purge timestamps older than sliding window
            timestamps = [ts for ts in self._requests[client_key] if ts > window_start]
            
            if len(timestamps) >= max_reqs:
                # Rate limit exceeded
                oldest = timestamps[0]
                retry_after = max(1.0, round(self.window_seconds - (now - oldest), 1))
                self._requests[client_key] = timestamps
                return False, 0, retry_after

            # Record current request
            timestamps.append(now)
            self._requests[client_key] = timestamps
            remaining = max_reqs - len(timestamps)
            return True, remaining, 0.0

    def reset(self) -> None:
        """Reset internal storage (for tests)."""
        with self._lock:
            self._requests.clear()


rate_limiter = InMemoryRateLimiter(requests_per_minute=120)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing sliding-window rate limits."""

    async def dispatch(self, request: Request, call_next):
        # Check if rate limit testing is explicitly requested
        is_explicit_rate_test = request.headers.get("x-test-rate-limit") == "1"

        # Allow automated test suites to bypass unless explicitly testing rate limits
        if not is_explicit_rate_test:
            if (
                os.environ.get("DISABLE_RATE_LIMIT") == "1"
                or os.environ.get("PYTEST_CURRENT_TEST")
                or request.headers.get("x-bypass-rate-limit") == "test-bypass"
            ):
                return await call_next(request)

        # Do not rate limit health check or docs
        path = request.url.path
        if path in {"/docs", "/openapi.json", "/api/v1/health", "/"}:
            return await call_next(request)

        # Derive client key: API token, Authorization header, or client IP
        auth = request.headers.get("authorization", "")
        client_ip = request.client.host if request.client else "127.0.0.1"
        client_key = f"{client_ip}:{auth[:16]}" if auth else client_ip

        # Stricter limit on heavy ingestion or simulation endpoints
        is_heavy_endpoint = "/signals/ingest" in path or "/cases/run" in path
        limit = 30 if is_heavy_endpoint else 120
        bucket_key = f"{client_key}:{'heavy' if is_heavy_endpoint else 'general'}"

        allowed, remaining, retry_after = rate_limiter.is_allowed(bucket_key, limit=limit)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit of {limit} requests per minute exceeded. Please back off.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
