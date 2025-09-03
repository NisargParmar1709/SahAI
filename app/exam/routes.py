from __future__ import annotations
import json
from datetime import datetime
from flask import render_template, request, flash
from flask_login import login_required, current_user
from ..extensions import limiter, db
from ..ai.tasks import exam_snack, check_crisis_paths
from ..model import SafetyEvent
from . import exam_bp
from app.utils.tracing import trace_route
from .forms import ExamQuestionForm


@exam_bp.route("/exam", methods=["GET", "POST"], endpoint="exam_copilot")
@login_required
@limiter.limit("30 per hour")
@trace_route("exam.exam_copilot")
def copilot():
    form = ExamQuestionForm()
    answer = None
    if form.validate_on_submit():
        q = (form.question.data or "").strip()
        crisis = check_crisis_paths(q)
        if crisis.triggered:
            ev = SafetyEvent(user_id=current_user.id, event_type="exam_crisis", event_details=json.dumps({"len": len(q)}))
            db.session.add(ev)
            db.session.commit()
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        qa = exam_snack(mode="focus", duration_sec=600, language=current_user.language_pref or "en")
        answer = qa.answer
        flash("Answer generated 🎓", "success")
    return render_template("exam/copilot.html", form=form, answer=answer)
