from __future__ import annotations
from flask import Blueprint

gratitude_bp = Blueprint("gratitude", __name__, template_folder="../templates", static_folder="../static")
