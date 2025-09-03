from __future__ import annotations
import json
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import comics_bp
from app.utils.tracing import trace_route
from .forms import ComicForm
from .services import save_panel_images
from ..extensions import db
from ..model import MediaAsset, SafetyEvent
from ..ai.tasks import generate_comic_script, check_crisis_paths


@comics_bp.route("/comics/new", methods=["GET", "POST"], endpoint="comics_new")
@login_required
@trace_route("comics.new")
def new_comic():
    form = ComicForm()
    if form.validate_on_submit():
        text = (form.situation.data or "").strip()
        crisis = check_crisis_paths(text)
        if crisis.triggered:
            ev = SafetyEvent(user_id=current_user.id, event_type="self_harm_detected",
                             event_details=json.dumps({"source": "comics"}))
            db.session.add(ev)
            db.session.commit()
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        script = generate_comic_script(
            text, current_user.language_pref or "en")
        panels_meta = script.get("panels", [])
        paths = save_panel_images(len(panels_meta) or 3)

        # Save each panel as a MediaAsset
        created_ids = []
        for idx, pth in enumerate(paths):
            meta = panels_meta[idx] if idx < len(panels_meta) else {
                "panel_caption": "Moment", "dialogue": "", "visual_style": "abstract"}
            asset = MediaAsset(
                user_id=current_user.id,
                kind="comic_panel",
                source="ai_generated",
                file_path=pth,
                caption=meta.get("panel_caption", "")[:255],
                meta_json=json.dumps({"script": meta}),
            )
            db.session.add(asset)
            db.session.flush()
            created_ids.append(asset.id)
        db.session.commit()
        flash("Comic created 🎭", "success")
        # Redirect to detail of first panel group view
        return redirect(url_for("comics.comics_detail", group=",".join(map(str, created_ids))))
    return render_template("comics/new.html", form=form)


@comics_bp.route("/comics/<group>", methods=["GET"], endpoint="comics_detail")
@login_required
@trace_route("comics.detail")
def detail(group: str):
    try:
        ids = [int(x) for x in group.split(",") if x.strip().isdigit()]
    except Exception:
        ids = []
    items = MediaAsset.query.filter(MediaAsset.id.in_(
        ids), MediaAsset.user_id == current_user.id).all()
    print(items)
    if not items:
        return redirect(url_for("comics.comics_new"))
    # Keep original order
    items.sort(key=lambda x: ids.index(x.id) if x.id in ids else 0)
    for it in items:
        try:
            it.meta = json.loads(it.meta_json or "{}")
        except Exception:
            it.meta = {}

    return render_template("comics/detail.html", items=items)
