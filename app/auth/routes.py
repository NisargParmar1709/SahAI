from __future__ import annotations
import os
import secrets
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, current_app
)
from app.logging_config import get_logger, log_extra_safe
from flask_login import login_user, logout_user, current_user
from sqlalchemy import or_

from ..extensions import db, login_manager, limiter
from ..model import User
from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.utils.tracing import trace_route

auth_bp = Blueprint("auth", __name__, template_folder="../templates")
log = get_logger("auth")

# User loader for Flask-Login


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


# --- Helpers -----------------------------------------------------------------
def _find_user_by_identity(identity: str) -> User | None:
    return User.query.filter(
        or_(User.username.ilike(identity.strip()),
            User.email.ilike(identity.strip()))
    ).first()


# --- Routes ------------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
@limiter.limit("5 per minute")
@trace_route("auth.register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.user_profile"))
    form = RegisterForm()
    if form.validate_on_submit():
        # Uniqueness checks
        if User.query.filter_by(username=form.username.data.strip()).first():
            form.username.errors.append("This username is already taken.")
        elif form.email.data and User.query.filter_by(email=form.email.data.strip()).first():
            form.email.errors.append("This email is already registered.")
        else:
            user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip() if form.email.data else None,
                language_pref="en",
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash("Welcome to SahAI! Your account is ready 💚", "success")
            return redirect(url_for("user.user_profile"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
@limiter.limit("500 per 10 minutes")
@trace_route("auth.login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user.user_profile"))

    form = LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            identity = form.username_or_email.data.strip()
            user = _find_user_by_identity(identity)

            if user and getattr(user, "is_active", True) and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                flash("Logged in successfully. Hi there 👋", "success")
                return redirect(url_for("user.user_profile"))

            # Invalid credentials
            log_extra_safe(log, "warning", "login_failed", extra={"id_len": len(identity)})
            flash("Invalid credentials. Please try again.", "danger")

        else:
            flash("Please fix the errors in the form.", "warning")

    # ✅ Always return a template at the end
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"], endpoint="logout")
@limiter.limit("20 per hour")
@trace_route("auth.logout")
def logout():
    print("entered")
    if not current_user.is_authenticated:
        return redirect(url_for("main.home"))
    logout_user()
    flash("You have been logged out. Take care 🌱", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/forgot", methods=["GET", "POST"], endpoint="auth_forgot")
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("user.user_profile"))

    form = ForgotPasswordForm()
    reset_url = None

    if form.validate_on_submit():
        user = _find_user_by_identity(form.username_or_email.data)
        if user:
            token = user.set_reset_token(expires_in_minutes=30)
            reset_url = url_for("auth.auth_reset", token=token, _external=True)
            current_app.logger.info(f"Dev Reset URL: {reset_url}")
            flash("A password reset link has been generated (dev mode).", "info")
        else:
            flash("If this account exists, a reset link will be generated.", "info")

    return render_template("auth/forgot_password.html", form=form, reset_url=reset_url)

@auth_bp.route("/reset/<token>", methods=["GET", "POST"], endpoint="auth_reset")
@limiter.limit("5 per hour")
def reset_password(token: str):
    form = ResetPasswordForm()
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.validate_reset_token(token):
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        flash("Password updated! You can log in now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)

