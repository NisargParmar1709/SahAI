from __future__ import annotations
import time
from functools import wraps
from flask import request, g
from .hash import user_hash
from app.logging_config import get_logger, log_extra_safe

log = get_logger("trace")

def trace_route(name: str | None = None):
    """Route tracing decorator preserving original function metadata.

    Parameters:
        name: Optional explicit trace name; defaults to module.fn.
    """
    def _decorator(fn):
        trace_name = name or f"{fn.__module__}.{fn.__name__}"

        @wraps(fn)
        def _wrapped(*args, **kwargs):
            rid = getattr(g, "request_id", None)
            uh = user_hash()
            t0 = time.perf_counter()
            status = 200
            try:
                resp = fn(*args, **kwargs)
                status = getattr(resp, "status_code", status)
                return resp
            finally:
                dt = int((time.perf_counter() - t0) * 1000)
                payload = {
                    "event": "route_trace",
                    "name": trace_name,
                    "request_id": rid,
                    "user_hash": uh,
                    "path": request.path,
                    "method": request.method,
                    "duration_ms": dt,
                    "status_code": status,
                }
                log_extra_safe(log, "info", "route_trace", extra=payload)
        return _wrapped
    return _decorator
