from __future__ import annotations
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..extensions import db, limiter
from ..model import PeerWallPost, SafetyEvent
from ..ai.tasks import check_crisis_paths
from . import peer_bp
from app.utils.tracing import trace_route
from .forms import PeerPostForm


@peer_bp.route("/peer", methods=["GET", "POST"], endpoint="peer_wall")
@login_required
@limiter.limit("50 per hour")
@trace_route("peer.peer_wall")
def wall():
    form = PeerPostForm()
    if form.validate_on_submit():
        text = (form.body.data or "").strip()
        crisis = check_crisis_paths(text)
        if crisis.triggered:
            ev = SafetyEvent(user_id=current_user.id, event_type="peer_crisis", event_details=json.dumps({"len": len(text)}))
            db.session.add(ev)
            db.session.commit()
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        post = PeerWallPost(user_id=current_user.id, body=text, created_at=datetime.utcnow())
        db.session.add(post)
        db.session.commit()
        flash("Posted anonymously 🌱", "success")
        return redirect(url_for("peer.peer_wall"))

    posts = PeerWallPost.query.order_by(PeerWallPost.created_at.desc()).limit(30).all()
    return render_template("peer/wall.html", form=form, posts=posts)
