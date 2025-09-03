from __future__ import annotations
from flask import Blueprint

demo_bp = Blueprint("demo", __name__, template_folder="../templates", static_folder="../static")
