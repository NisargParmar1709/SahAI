from __future__ import annotations
from flask import Blueprint

wellness_bp = Blueprint("wellness", __name__, template_folder="../templates", static_folder="../static")
