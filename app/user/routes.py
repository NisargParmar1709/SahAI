from __future__ import annotations
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..extensions import db
from app.utils.tracing import trace_route
from ..model import User

user_bp = Blueprint("user", __name__, template_folder="../templates")


def _allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in current_app.config["UPLOAD_EXTENSIONS"]


def _randomized_name(filename: str) -> str:
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{name[:20]}_{secrets.token_hex(6)}{ext}"


@user_bp.route("/profile", endpoint="user_profile")
@login_required
@trace_route("user.user_profile")
def profile():
    # Profile completeness (simple heuristic)
    completeness = 0
    if current_user.display_name:
        completeness += 30
    if current_user.bio:
        completeness += 30
    if current_user.avatar_path:
        completeness += 40
    completeness = min(completeness, 100)
    return render_template("user/profile.html", completeness=completeness)


@user_bp.route("/profile/edit", methods=["GET", "POST"], endpoint="user_profile_edit")
@login_required
@trace_route("user.user_profile_edit")
def profile_edit():
    if request.method == "POST":
        display_name = (request.form.get("display_name") or "").strip()[:120]
        bio = (request.form.get("bio") or "").strip()[:500]
        language = (request.form.get("language") or "en").strip().lower()
        remove_avatar = bool(request.form.get("remove_avatar"))

        # Validate language
        if language not in {"en", "hi", "hinglish"}:
            flash("Invalid language choice.", "danger")
            return redirect(url_for("user.user_profile_edit"))

        # Avatar upload
        file = request.files.get("avatar")
        avatar_path = current_user.avatar_path
        if file and file.filename:
            if not _allowed_file(file.filename):
                flash("Only PNG/JPG images are allowed (<= 1MB).", "danger")
                return redirect(url_for("user.user_profile_edit"))
            filename = _randomized_name(file.filename)
            upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
            upload_dir.mkdir(parents=True, exist_ok=True)
            save_path = upload_dir / filename
            file.save(save_path)
            avatar_path = f"static/uploads/{filename}"

        if remove_avatar:
            avatar_path = None

        current_user.display_name = display_name or None
        current_user.bio = bio or None
        current_user.language_pref = language
        current_user.avatar_path = avatar_path
        db.session.commit()
        flash("Profile updated 💚", "success")
        return redirect(url_for("user.user_profile"))

    return render_template("user/profile_edit.html")


@user_bp.route("/privacy", methods=["GET", "POST"], endpoint="user_privacy")
@login_required
@trace_route("user.privacy")
def privacy():
    if request.method == "POST":
        current_user.consent_analytics = bool(request.form.get("consent_analytics"))
        current_user.consent_research = bool(request.form.get("consent_research"))
        db.session.commit()
        flash("Privacy settings saved.", "success")
        return redirect(url_for("user.user_privacy"))
    return render_template("user/privacy.html")


@user_bp.route("/change-password", methods=["GET", "POST"], endpoint="user_change_password")
@login_required
@trace_route("user.change_password")
def change_password():
    if request.method == "POST":
        old = request.form.get("old_password") or ""
        new = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""
        if not current_user.check_password(old):
            flash("Old password is incorrect.", "danger")
            return redirect(url_for("user.user_change_password"))
        if len(new) < 8 or not any(c.isalpha() for c in new) or not any(c.isdigit() for c in new):
            flash("New password must be 8+ chars with letters and numbers.", "danger")
            return redirect(url_for("user.change_password"))
        if new != confirm:
            flash("Password confirmation does not match.", "danger")
            return redirect(url_for("user.change_password"))
        current_user.set_password(new)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("user.user_profile"))
    return render_template("user/change_password.html")
