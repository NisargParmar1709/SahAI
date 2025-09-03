from __future__ import annotations
import uuid
from flask import g, request
from app.logging_config import get_logger, log_extra_safe

log = get_logger("request_id")

def register_request_id(app):
    header_name = app.config.get("REQUEST_ID_HEADER", "X-Request-ID")

    @app.before_request
    def _assign_request_id():
        rid = request.headers.get(header_name) or str(uuid.uuid4())
        g.request_id = rid

    @app.after_request
    def _inject_response_id(resp):
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers[header_name] = rid
        return resp
