from __future__ import annotations
from flask import Blueprint

comics_bp = Blueprint("comics", __name__, template_folder="../templates", static_folder="../static")
