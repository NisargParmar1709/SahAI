from __future__ import annotations
from typing import List
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_limiter.util import get_remote_address

from app.ai.exceptions import AIUnavailableError
from app.model import db

from . import questions_bp
from app.utils.tracing import trace_route
from .forms import AskQuestionForm
from ..extensions import db, limiter
from ..model import QuestionBoxItem
from ..ai.tasks import moderate_and_rewrite_peer_post, answer_user_question, check_crisis_paths


def _simple_paginate(query, page: int, per_page: int = 10):
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    total = query.order_by(None).count()
    pages = max(1, (total + per_page - 1) // per_page)
    class P: pass
    p = P()
    p.items = items
    p.page = page
    p.pages = pages
    p.has_next = page < pages
    p.has_prev = page > 1
    p.next_num = page + 1 if p.has_next else page
    p.prev_num = page - 1 if p.has_prev else 1
    return p


@questions_bp.route("/questions/ask", methods=["GET", "POST"], endpoint="questions_ask")
@login_required
@limiter.limit("3 per hour", key_func=lambda: str(current_user.id) if current_user.is_authenticated else get_remote_address())
@trace_route("questions.ask")
def ask():
    form = AskQuestionForm()
    # default language from profile
    if request.method == "GET":
        form.language.data = current_user.language_pref or "en"

    if form.validate_on_submit():
        text = (form.question_text.data or "").strip()
        language = form.language.data or "en"

        # Crisis check BEFORE any AI
        crisis = check_crisis_paths(text)
        if crisis.triggered:
            flash("We noticed crisis words — showing grounding steps 💙", "warning")
            # do not persist raw; show supportive modal page
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        try:
            # Moderate first
            mod = moderate_and_rewrite_peer_post(text, language)
            if not mod.safe:
                item = QuestionBoxItem(
                    user_id=current_user.id,
                    question_text=text,
                    ai_answer_text=None,
                    language=language,
                    status="flagged",
                    is_flagged=True,
                    flag_reason=mod.reason[:255] if mod.reason else "unsafe",
                )
                db.session.add(item)
                db.session.commit()
                flash("Your question seems sensitive. We’ve flagged it for safety; please try a different phrasing.", "warning")
                return redirect(url_for("questions.detail", item_id=item.id))

            # Safe → Answer
            answer = answer_user_question(mod.suggested_rewrite or text, language)
            item = QuestionBoxItem(
                user_id=current_user.id,
                question_text=mod.suggested_rewrite or text,
                ai_answer_text=answer.answer,
                language=answer.language or language,
                status="answered",
                is_flagged=False,
                flag_reason=None,
            )
            db.session.add(item)
            db.session.commit()
            flash("Answer ready ✅", "success")
            return redirect(url_for("questions.questions_detail", item_id=item.id))
        except AIUnavailableError:
            item = QuestionBoxItem(
                user_id=current_user.id,
                question_text=text,
                ai_answer_text=None,
                language=language,
                status="pending",
                is_flagged=False,
            )
            db.session.add(item)
            db.session.commit()
            flash("Our moderation service is unavailable — your question has been saved and will be processed soon.", "warning")
            return redirect(url_for("questions.questions_detail", item_id=item.id))

    return render_template("questions/ask.html", form=form)


@questions_bp.route("/questions", methods=["GET"], endpoint="questions_list")
@login_required
@trace_route("questions.list")
def list_items():
    page = max(1, int(request.args.get("page", 1)))
    q = QuestionBoxItem.query.filter_by(user_id=current_user.id).order_by(QuestionBoxItem.created_at.desc())
    pagination = _simple_paginate(q, page=page, per_page=10)
    return render_template("questions/list.html", pagination=pagination)


@questions_bp.route("/questions/<int:item_id>", methods=["GET"], endpoint="questions_detail")
@login_required
@trace_route("questions.questions_detail")
def detail(item_id: int):
    item = QuestionBoxItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    return render_template("questions/detail.html", item=item)
