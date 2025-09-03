from __future__ import annotations
import json, logging, os, sys, time, hashlib
from typing import Any, Dict
from .logging_sanitize import sanitize_extra
from flask import g, has_request_context, request
from flask_login import current_user

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        base: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.msg if isinstance(record.msg, str) else record.getMessage()),
        }
        if has_request_context():
            rid = getattr(g, "request_id", None)
            base["request_id"] = rid
            base["method"] = request.method
            base["path"] = request.path
            try:
                if current_user.is_authenticated:  # type: ignore[attr-defined]
                    base["user_hash"] = hashlib.sha256(str(current_user.id).encode()).hexdigest()[:12]
                else:
                    base["user_hash"] = "anon"
            except Exception:
                base["user_hash"] = "anon"
        # Merge extra fields
        for k, v in record.__dict__.items():
            if k.startswith('_') or k in base or k in ("args","msg","exc_info","exc_text","lineno","pathname","filename","module","funcName","stack_info","created","msecs","relativeCreated","levelno","thread","threadName","process","processName","name"):
                continue
            base[k] = v
        if record.exc_info:
            base["error_class"] = record.exc_info[0].__name__
            base["error_message"] = str(record.exc_info[1])
        return json.dumps(base, ensure_ascii=False)

def init_logging(app):
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    json_mode = app.config.get("DEBUG_LOG_JSON", True)
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(level)
    formatter: logging.Formatter
    if json_mode:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    stream.setLevel(level)
    root.addHandler(stream)
    # keep Flask's app.logger consistent
    app.logger.handlers = [stream]
    app.logger.setLevel(level)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def log_extra_safe(logger: logging.Logger, level: str, msg: str, *, extra: Dict[str, Any] | None = None, **kwargs):
    safe = sanitize_extra(extra)
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(msg, extra=safe, **kwargs)
