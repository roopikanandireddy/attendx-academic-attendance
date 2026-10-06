"""
AttendX — Module 8 Observability & Structured Request Timing
Provides request correlation IDs (X-Request-ID), high-resolution request timing,
database query execution timing, error classification, slow-request detection,
and Render-safe JSON structured logging.
"""
import asyncio
import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional, Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.config import get_settings

# Context variables for request tracing & DB duration
request_id_ctx: ContextVar[str] = ContextVar("request_id_ctx", default="")
db_duration_ctx: ContextVar[float] = ContextVar("db_duration_ctx", default=0.0)

# Request ID sanitization pattern (UUIDs, alphanumeric, hyphens, underscores up to 128 chars)
SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")

# Dedicated logger for structured HTTP access events
logger = logging.getLogger("attendx.access")
logger.setLevel(logging.INFO)

# Ensure stdout handler exists and outputs single-line JSON
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def sanitize_or_generate_request_id(incoming_header: Optional[str]) -> str:
    """
    Validate incoming X-Request-ID against a safe pattern to prevent header injection.
    Generates a secure UUID v4 if missing or invalid.
    """
    if incoming_header:
        trimmed = incoming_header.strip()
        if SAFE_REQUEST_ID_REGEX.match(trimmed):
            return trimmed
    return str(uuid.uuid4())


def get_current_request_id() -> str:
    """Retrieve the correlation ID of the currently executing request."""
    return request_id_ctx.get()


def classify_http_status(status_code: int) -> str:
    """
    Categorize HTTP status codes into semantic groups.
    Distinguishes authentication, authorization, validation, client, and server errors.
    """
    if status_code < 400:
        return "SUCCESS"
    if status_code == 401:
        return "AUTHENTICATION_ERROR"
    if status_code == 403:
        return "AUTHORIZATION_ERROR"
    if status_code in (400, 422):
        return "VALIDATION_ERROR"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT_ERROR"
    if 400 <= status_code < 500:
        return "CLIENT_ERROR"
    return "SERVER_ERROR"


def get_normalized_route(request: Request) -> str:
    """
    Extract route template (e.g. /api/admin/students/{id}) or clean path.
    Omits query strings completely to prevent leaking tokens or search terms.
    """
    route = request.scope.get("route")
    if route and hasattr(route, "path") and route.path:
        return str(route.path)
    return str(request.url.path)


def log_structured_request(
    request_id: str,
    method: str,
    route: str,
    status: int,
    duration_ms: float,
    db_duration_ms: float,
    slow: bool,
    category: str,
    level: str = "INFO",
    error_detail: Optional[str] = None,
) -> None:
    """
    Emit a structured JSON log entry to stdout without exposing secrets.
    """
    settings = get_settings()
    if not getattr(settings, "ENABLE_STRUCTURED_LOGGING", True):
        return

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": "http_request",
        "request_id": request_id,
        "method": method,
        "route": route,
        "status": status,
        "duration_ms": duration_ms,
        "db_duration_ms": db_duration_ms,
        "slow": slow,
        "category": category,
    }
    if error_detail:
        payload["error_type"] = error_detail

    log_line = json.dumps(payload, separators=(",", ":"))
    if level == "ERROR":
        logger.error(log_line)
    elif level == "WARNING":
        logger.warning(log_line)
    else:
        logger.info(log_line)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware capturing request start, correlation ID, database execution time,
    duration in milliseconds, slow-request detection, and structured JSON logs.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raw_header = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
        request_id = sanitize_or_generate_request_id(raw_header)

        # Bind context variables
        req_token = request_id_ctx.set(request_id)
        db_token = db_duration_ctx.set(0.0)
        request.state.request_id = request_id

        settings = get_settings()
        slow_threshold_ms = getattr(settings, "SLOW_REQUEST_THRESHOLD_MS", 1000.0)
        start_time = time.perf_counter()
        status_code = 500
        response: Optional[Response] = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected / request cancelled — not an application or server failure
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            db_duration_ms = round(db_duration_ctx.get(), 2)
            log_structured_request(
                request_id=request_id,
                method=request.method,
                route=get_normalized_route(request),
                status=499,
                duration_ms=duration_ms,
                db_duration_ms=db_duration_ms,
                slow=duration_ms >= slow_threshold_ms,
                category="CANCELLED",
                level="INFO",
            )
            raise
        except Exception as exc:
            # Unhandled server exception
            status_code = 500
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            db_duration_ms = round(db_duration_ctx.get(), 2)
            slow = duration_ms >= slow_threshold_ms
            log_structured_request(
                request_id=request_id,
                method=request.method,
                route=get_normalized_route(request),
                status=500,
                duration_ms=duration_ms,
                db_duration_ms=db_duration_ms,
                slow=slow,
                category="SERVER_ERROR",
                level="ERROR",
                error_detail=exc.__class__.__name__,
            )
            json_response = JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred. Please try again later."},
            )
            json_response.headers["X-Request-ID"] = request_id
            return json_response
        finally:
            if response is not None:
                duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                db_duration_ms = round(db_duration_ctx.get(), 2)
                slow = duration_ms >= slow_threshold_ms
                category = classify_http_status(status_code)
                level = "ERROR" if status_code >= 500 else ("WARNING" if slow else "INFO")

                log_structured_request(
                    request_id=request_id,
                    method=request.method,
                    route=get_normalized_route(request),
                    status=status_code,
                    duration_ms=duration_ms,
                    db_duration_ms=db_duration_ms,
                    slow=slow,
                    category=category,
                    level=level,
                )
                response.headers["X-Request-ID"] = request_id

            request_id_ctx.reset(req_token)
            db_duration_ctx.reset(db_token)

        return response


def setup_db_timing_hooks(engine) -> None:
    """
    Safely attach execution listeners to SQLAlchemy engine to measure aggregate query time
    per request context. Does NOT inspect SQL text or parameters to ensure zero credential leakage.
    """
    from sqlalchemy import event

    @event.listens_for(engine, "before_cursor_execute")
    def on_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_stack", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def on_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        stack = conn.info.get("query_start_stack")
        if stack:
            start = stack.pop()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            current = db_duration_ctx.get()
            db_duration_ctx.set(current + elapsed_ms)

    @event.listens_for(engine, "handle_error")
    def on_handle_error(exception_context):
        conn = exception_context.connection
        if conn:
            stack = conn.info.get("query_start_stack")
            if stack:
                start = stack.pop()
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                current = db_duration_ctx.get()
                db_duration_ctx.set(current + elapsed_ms)
