from __future__ import annotations
import traceback
from flask import Blueprint, render_template, request, g, current_app
from werkzeug.exceptions import HTTPException, NotFound
from app.logging_config import get_logger, log_extra_safe
from app.utils.hash import user_hash

errors_bp = Blueprint("errors", __name__)
log = get_logger("errors")

@errors_bp.app_errorhandler(404)
def not_found(e: NotFound):
    rid = getattr(g, "request_id", None)
    payload = {"event":"http_404","request_id":rid,"path":request.path,"method":request.method,"user_hash":user_hash(),"status":404}
    log_extra_safe(log, "warning", "http_404", extra=payload)
    return render_template("errors/404.html", request_id=rid), 404

@errors_bp.app_errorhandler(Exception)
def handle_exception(e: Exception):  # pragma: no cover
    rid = getattr(g, "request_id", None)
    code = 500
    if isinstance(e, HTTPException):
        code = e.code or 500
    payload = {
        "event":"app_error",
        "error_class": e.__class__.__name__,
        "request_id": rid,
        "path": request.path,
        "method": request.method,
        "status_code": code,
        "user_hash": user_hash(),
    }
    log_extra_safe(log, "error", "app_error", extra=payload, exc_info=current_app.debug)
    if code == 404:
        return render_template("errors/404.html", request_id=rid), 404
    return render_template("errors/500.html", request_id=rid), code
