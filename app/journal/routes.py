from __future__ import annotations
import json
from datetime import datetime, timedelta
from typing import Dict, List

from flask import (
    render_template, request, redirect, url_for, flash, current_app, abort
)
from flask_login import login_required, current_user

from . import journal_bp
from app.utils.tracing import trace_route
from .forms import NewJournalForm
from ..extensions import db, limiter
from ..model import JournalEntry, EmotionSnapshot, SafetyEvent
from ..services.db_helpers import list_paginated, get_or_404
from ..ai.tasks import prepare_journal_insights, check_crisis_paths
from ..ai.exceptions import AITimeoutError, AIUnavailableError, AIStructuredOutputError, AIConfigError
import traceback
from app.logging_config import log_extra_safe, get_logger
_jlog = get_logger("journal")


# ---------------------------
# Helpers
# ---------------------------
def _ensure_owner(entry: JournalEntry) -> None:
    if entry.user_id != current_user.id:
        abort(404)


def _primary_from_scores(scores: Dict[str, float]) -> str:
    if not scores:
        return "neutral"
    return max(scores.items(), key=lambda kv: kv[1])[0]


# ---------------------------
# Routes
# ---------------------------
@journal_bp.route("/journal/new", methods=["GET", "POST"], endpoint="journal_new")
@login_required
@limiter.limit("20 per hour")
@trace_route("journal.journal_new")
def new():


    from ..ai.exceptions import AITimeoutError, AIUnavailableError, AIStructuredOutputError, AIConfigError

    form = NewJournalForm()
    entry: JournalEntry | None = None  # defensive initialization
    if form.validate_on_submit():
        text = (form.text.data or "").strip()
        if not text:
            flash("Please write something first.", "warning")
            return render_template("journal/new.html", form=form)
        if len(text) > 2000:
            text = text[:2000]
        language = current_user.language_pref or "en"
        store_raw_flag = bool(form.store_raw.data)

        # Crisis check (if triggered, we do not proceed with AI)
        crisis = check_crisis_paths(text)
        
        if crisis.triggered:
            ev = SafetyEvent(
                user_id=current_user.id,
                event_type="self_harm_detected",
                event_details=json.dumps({"source": "journal", "len": len(text)}),
            )
            db.session.add(ev)
            db.session.commit()
            flash("We noticed you might need extra care. Here are grounding steps 💙", "warning")
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        try:
            summary, emotions, keywords = prepare_journal_insights(text=text, language=language, store_raw=store_raw_flag)
            print(summary)
        except (AITimeoutError, AIUnavailableError, AIStructuredOutputError, AIConfigError) as e:
            log_extra_safe(
                _jlog, "warning", "journal_ai_fail",
                extra={"event": "journal_ai_fail", "len": len(text), "lang": language, "etype": type(e).__name__}
            )
            # fallback: no AI insights
            entry = JournalEntry(
                user_id=current_user.id,
                raw_text=text if store_raw_flag else None,
                store_raw=store_raw_flag,
                ai_summary="",
                ai_emotions="[]",
                ai_keywords="[]",
                visibility="private",
                is_deleted=False,
            )
            try:
                db.session.add(entry)
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("Could not save your entry. Please try again.", "danger")
                return render_template("journal/new.html", form=form)

            flash("AI insights could not be generated. Please try again.", "warning")
            return redirect(url_for("journal.journal_detail", entry_id=entry.id))

        except Exception as e:  # Other unanticipated errors -> do not save, surface generic
            # Capture a short, sanitized traceback snippet (no user text) for debugging
            tb_snip = " | ".join(traceback.format_exception_only(type(e), e)).strip()
            log_extra_safe(
                _jlog,
                "error",
                "journal_unexpected_fail",
                extra={"etype": type(e).__name__, "err": tb_snip},
            )
            flash("Unexpected error generating insights.", "danger")
            print(e)
            return render_template("journal/new.html", form=form)
        else:
            # Persist entry (raw only if opted in)
            entry = JournalEntry(
                user_id=current_user.id,
                raw_text=text if store_raw_flag else None,
                store_raw=store_raw_flag,
                ai_summary=summary.summary[:2000],
                ai_emotions=json.dumps(summary.detected_emotions or []),
                ai_keywords=json.dumps(keywords or []),
                visibility="private",
                is_deleted=False,
            )
            try:
                db.session.add(entry)
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("Could not save your entry. Please try again.", "danger")
                return render_template("journal/new.html", form=form)

            # Emotion snapshot only if we have numeric scores
            if emotions.scores:
                try:
                    snap = EmotionSnapshot(
                        user_id=current_user.id,
                        source="journal",
                        score_map=json.dumps(emotions.scores or {}),
                        label=emotions.primary_label or _primary_from_scores(emotions.scores or {}),
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(snap)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    log_extra_safe(_jlog, "warning", "emotion_snapshot_save_failed", extra={"uid": current_user.id})

            flash("Journal saved with AI insights ✨", "success")
            return redirect(url_for("journal.journal_detail", entry_id=entry.id))
    return render_template("journal/new.html", form=form)


@journal_bp.route("/journal", methods=["GET"], endpoint="journal_list")
@login_required
@trace_route("journal.list")
def journal_emotion_lens():
    page = max(1, int(request.args.get("page", 1)))
    per_page = 9
    pagination = list_paginated(JournalEntry, user_id=current_user.id, page=page, per_page=per_page, order="-created_at")
    return render_template("journal/list.html", pagination=pagination)


@journal_bp.route("/journal/<int:entry_id>", methods=["GET"], endpoint="journal_detail")
@login_required
@trace_route("journal.journal_detail")
def detail(entry_id: int):
    entry = get_or_404(JournalEntry, id=entry_id)
    _ensure_owner(entry)
    # Derive chips for emotions/keywords
    emotions = []
    try:
        emotions = json.loads(entry.ai_emotions) if entry.ai_emotions else []
    except Exception:
        emotions = []
    keywords = []
    try:
        keywords = json.loads(entry.ai_keywords) if entry.ai_keywords else []
    except Exception:
        keywords = []
    return render_template("journal/detail.html", entry=entry, emotions=emotions, keywords=keywords)


@journal_bp.route("/journal/<int:entry_id>/delete", methods=["POST"], endpoint="journal_delete")
@login_required
@trace_route("journal.delete")
def delete_entry(entry_id: int):
    entry = get_or_404(JournalEntry, id=entry_id)
    _ensure_owner(entry)
    entry.is_deleted = True
    db.session.commit()
    flash("Entry moved to private archive.", "info")
    return redirect(url_for("journal.journal_emotion_lens"))


# ---------------------------
# Emotion Lens Dashboard
# ---------------------------
@journal_bp.route("/dashboard/emotions", methods=["GET"], endpoint="journal_emotion_lens")
@login_required
@trace_route("journal.emotion_lens")
def emotion_lens():
    """Aggregate last 30 days EmotionSnapshot for the current user and render charts."""
    since = datetime.utcnow() - timedelta(days=30)
    snaps: List[EmotionSnapshot] = (
        EmotionSnapshot.query
        .filter(EmotionSnapshot.user_id == current_user.id)
        .filter(EmotionSnapshot.created_at >= since)
        .order_by(EmotionSnapshot.created_at.asc())
        .all()
    )

    # Prepare data for charts
    daily = []
    dist_counts: Dict[str, int] = {}
    heat_days = []
    heat_values = []

    key_order = [
    "calm",
    "anxious",
    "sad",
    "angry",
    "hopeful",
    "tired",
    "stressed",
    "motivated",
    "happy",
    "lonely",
    "confused",
    "grateful",
    "excited",
    "frustrated",
    "guilty",
    "embarrassed",
    "insecure",
    "relieved",
    "proud",
]

    for s in snaps:
        scores = {}
        try:
            scores = json.loads(s.score_map or "{}")
        except Exception:
            scores = {}
        label = s.label or _primary_from_scores(scores)
        dist_counts[label] = dist_counts.get(label, 0) + 1

        primary_score = scores.get(label, max(scores.values()) if scores else 0)
        daily.append({"date": s.created_at.strftime("%Y-%m-%d"), "label": label, "score": round(float(primary_score or 0), 3)})

        # Heatmap rows in fixed key order
        heat_days.append(s.created_at.strftime("%Y-%m-%d"))
        heat_values.append([round(float(scores.get(k, 0)), 3) for k in key_order])

    # Today’s primary
    todays = daily[-1]["label"] if daily else "—"

    # Friendly micro-summary (no extra AI call)
    micro = "A gentle, steady week." if dist_counts.get("calm", 0) >= dist_counts.get("anxious", 0) else \
            "It’s been a mixed week—great job showing up for yourself."

    return render_template(
        "dashboard/emotion_lens.html",
        daily=daily,
        heat_days=heat_days,
        heat_values=heat_values,
        dist_counts=dist_counts,
        key_order=key_order,
        todays=todays,
        micro=micro,
    )
