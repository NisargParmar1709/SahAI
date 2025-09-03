from __future__ import annotations
from flask import Blueprint, jsonify
from .gemini_client import get_ai_client
from .exceptions import AIConfigError

ai_health_bp = Blueprint("ai_health", __name__)


@ai_health_bp.route("/_health/ai", methods=["GET"], endpoint="ai_health")
def ai_health():  # pragma: no cover - lightweight endpoint
    try:
        client = get_ai_client()
        info = client.health_probe()
        status = 200 if info.get("ok") else 503
        return jsonify(info), status
    except AIConfigError:
        return jsonify({"ok": False, "meta": {"error": "config"}}), 503
    except Exception:
        return jsonify({"ok": False, "meta": {"error": "unexpected"}}), 503