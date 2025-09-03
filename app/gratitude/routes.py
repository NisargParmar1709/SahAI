from __future__ import annotations
from datetime import datetime, date, timedelta

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import gratitude_bp
from app.utils.tracing import trace_route
from .forms import GratitudeForm
from ..extensions import db, limiter
from ..model import GratitudeEntry, SafetyEvent
from ..ai.tasks import check_crisis_paths


def _date_only(dt: datetime) -> date:
    return (dt or datetime.utcnow()).date()


def _calculate_streaks(entries: list[GratitudeEntry]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) given entries sorted desc by created_at."""
    if not entries:
        return 0, 0
    days = sorted({_date_only(e.created_at) for e in entries}, reverse=True)
    longest = cur = 1
    for i in range(1, len(days)):
        if days[i] == days[i - 1] - timedelta(days=1):
            cur += 1
        else:
            longest = max(longest, cur)
            cur = 1
    longest = max(longest, cur)
    # current streak counts from today/backwards if continuous
    today = date.today()
    cur_streak = 0
    dset = set(days)
    while today - timedelta(days=cur_streak) in dset:
        cur_streak += 1
    return cur_streak, longest


@gratitude_bp.route("/gratitude", methods=["GET", "POST"], endpoint="gratitude_index")
@login_required
@limiter.limit("30 per hour")
@trace_route("gratitude.gratitude_index")
def index():
    form = GratitudeForm()
    # Has today’s entry?
    has_today = (
        GratitudeEntry.query.filter_by(user_id=current_user.id, is_deleted=False)
        .filter(GratitudeEntry.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
        .first()
        is not None
    )

    if form.validate_on_submit() and not has_today:
        text = (form.content.data or "").strip()
        # Crisis guard
        crisis = check_crisis_paths(text)
        if crisis.triggered:
            ev = SafetyEvent(user_id=current_user.id, event_type="self_harm_detected", event_details='{"source":"gratitude"}')
            db.session.add(ev)
            db.session.commit()
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        ge = GratitudeEntry(user_id=current_user.id, content=text)
        db.session.add(ge)
        db.session.commit()
        flash("Leaf added to your Gratitude Tree 🌱", "success")
        return redirect(url_for("gratitude.gratitude_index"))

    entries = (
        GratitudeEntry.query.filter_by(user_id=current_user.id, is_deleted=False)
        .order_by(GratitudeEntry.created_at.desc())
        .all()
    )
    cur, longest = _calculate_streaks(entries)
    leaves_count = len(entries)
    return render_template(
        "gratitude/index.html",
        form=form,
        has_today=has_today,
        leaves_count=leaves_count,
        entries=entries[:12],  # recent list
        current_streak=cur,
        longest_streak=longest,
    )
