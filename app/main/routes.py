from flask import Blueprint, render_template
from app.utils.tracing import trace_route

about_bp = Blueprint("about", __name__)

@about_bp.route("/about", endpoint="about_page")
@trace_route("main.about_page")
def about():
    return render_template("main/about.html")
