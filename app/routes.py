"""Main routes and error handlers for SahAI."""
from __future__ import annotations
from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    current_app.logger.debug("Rendering home page")
    return render_template("home.html")


def register_error_pages(app):
    """Attach custom error handlers with empathetic messaging."""

    @app.errorhandler(404)
    def not_found(error):  # noqa: ANN001
        app.logger.warning("404 Not Found")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):  # noqa: ANN001
        app.logger.error("500 Internal Server Error", exc_info=True)
        return render_template("500.html"), 500
