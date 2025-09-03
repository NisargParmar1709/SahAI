from __future__ import annotations
from flask import Blueprint

letters_bp = Blueprint("letters", __name__, template_folder="../templates", static_folder="../static")
