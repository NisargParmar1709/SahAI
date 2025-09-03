from __future__ import annotations
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import letters_bp
from app.utils.tracing import trace_route
from .forms import LetterForm
from ..extensions import db
from ..model import FutureLetter
from ..ai.tasks import summarize_journal  # reuse summarizer for unlocked reflection
from ..ai.tasks import check_crisis_paths


@letters_bp.route("/letters/new", methods=["GET", "POST"], endpoint="letters_new")
@login_required
@trace_route("letters.new")
def new_letter():
    form = LetterForm()
    if form.validate_on_submit():
        text = (form.letter_text.data or "").strip()
        crisis = check_crisis_paths(text)
        if crisis.triggered:
            # Do not persist raw potentially risky text
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        letter = FutureLetter(
            user_id=current_user.id,
            title=form.title.data.strip(),
            letter_text=text,
            open_after=datetime.combine(form.open_after.data, datetime.min.time()),
            is_opened=False,
        )
        db.session.add(letter)
        db.session.commit()
        flash("Future letter saved ✉️", "success")
        return redirect(url_for("letters.letters_new"))
    return render_template("letters/new.html", form=form)


@letters_bp.route("/letters", methods=["GET"], endpoint="letters_list")
@login_required
@trace_route("letters.list")
def list_letters():
    items = FutureLetter.query.filter_by(user_id=current_user.id).order_by(FutureLetter.open_after.asc()).all()
    now = datetime.utcnow()
    return render_template("letters/list.html", items=items, now=now)


@letters_bp.route("/letters/<int:letter_id>", methods=["GET"], endpoint="letters_detail")
@login_required
@trace_route("letters.detail")
def detail(letter_id: int):
    item = FutureLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    now = datetime.utcnow()
    is_open = now >= item.open_after
    reflection = None
    if is_open and not item.is_opened:
        # First open → create a reflection summary (safe, supportive)
        try:
            js = summarize_journal(item.letter_text[:2000], current_user.language_pref or "en", store_raw=True)
            reflection = js.summary
        except Exception:
            reflection = "A moment to notice your growth and values. Stay kind to yourself."
        item.is_opened = True
        item.opened_at = now
        db.session.commit()
    elif is_open and item.is_opened:
        # already opened, render again; optional: no extra call
        pass
    return render_template("letters/detail.html", item=item, is_open=is_open, reflection=reflection, now=now)
