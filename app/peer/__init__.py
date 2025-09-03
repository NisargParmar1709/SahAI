from flask import Blueprint

peer_bp = Blueprint("peer", __name__, template_folder="../templates", static_folder="../static")
