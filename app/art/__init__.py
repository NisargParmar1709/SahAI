from __future__ import annotations
from flask import Blueprint

art_bp = Blueprint("art", __name__, template_folder="../templates", static_folder="../static")
