from __future__ import annotations
import base64
import io
import json
import secrets
from datetime import datetime
from typing import List, Dict

from flask import render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user

from . import wellness_bp
from app.utils.tracing import trace_route
from ..extensions import db, limiter
from ..model import EmotionSnapshot, MeditationScript, Doodle, CulturalStory as StoryModel, ResiliencePrompt, SafetyEvent
from ..ai.tasks import (
    build_meditation_for_user, vision_describe_image, generate_cultural_story, create_resilience_prompts, check_crisis_paths, NoMoodSelectedError
)
from app.utils.mood_resolver import latest_detected_mood_for_current_user
from .forms import MeditationForm, DoodleUploadForm, StoryForm, ResilienceContextForm


# -------- Helpers --------
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg"}


def _latest_emotion_label() -> str | None:
    return latest_detected_mood_for_current_user()


def _infer_label_from_text(text: str) -> str:
    low = (text or "").lower()
    for k in [
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
    ]:
        if k in low:
            return k

    return None


def _save_image_from_data_url(data_url: str) -> tuple[bool, str | None, str]:
    """
    Accepts a data URL like: data:image/png;base64,XXXXX
    Validates type/size and writes to uploads folder with a random filename.
    """
    if not data_url or not data_url.startswith("data:"):
        return False, None, "Invalid image data."

    header, b64data = data_url.split(",", 1)
    mime = header.split(";")[0].replace("data:", "")
    if mime not in ALLOWED_IMAGE_TYPES:
        return False, None, "Unsupported image type."

    try:
        raw = base64.b64decode(b64data, validate=True)
    except Exception:
        return False, None, "Could not decode image."

    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 1 * 1024 * 1024)
    if len(raw) > max_bytes:
        return False, None, "Image too large (max 1MB)."

    # Persist
    ext = ".png" if mime == "image/png" else ".jpg"
    fname = f"doodle_{secrets.token_hex(8)}{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    import os
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, fname)
    with open(path, "wb") as f:
        f.write(raw)

    rel_path = f"uploads/{fname}"  # relative to app/static
    return True, rel_path, ""


# -------- Routes: Meditation --------
@wellness_bp.route("/wellness/meditation", methods=["GET", "POST"], endpoint="wellness_meditation")
@login_required
@limiter.limit("30 per hour")
@trace_route("wellness.wellness_meditation")
def meditation():
    form = MeditationForm()
    detected = _latest_emotion_label()
    chosen_emotions: List[str] = []
    plan = None

    if request.method == "POST" and form.validate_on_submit():
        raw_emotions = (form.emotions.data or "").strip()
        chosen_emotions = [e.strip().lower() for e in raw_emotions.split(",") if e.strip()]
        if not chosen_emotions and detected:
            chosen_emotions = [detected]
        if not chosen_emotions:
            flash("Please choose a mood before generating a meditation.", "warning")
        else:
            try:
                duration = int(form.duration_hint.data or "180")
                plan = build_meditation_for_user(chosen_emotions, duration, current_user.language_pref or "en")
                ms = MeditationScript(
                    user_id=current_user.id,
                    context_mood=",".join(chosen_emotions),
                    script_text="\n".join(plan.steps),
                    duration_sec=int(plan.duration_sec),
                )
                db.session.add(ms)
                db.session.commit()
                flash("Meditation ready 🌿", "success")
            except NoMoodSelectedError:
                flash("Mood selection required.", "warning")

    return render_template("wellness/meditation.html", form=form, detected=detected, chosen_emotions=chosen_emotions, plan=plan)


# -------- Routes: Doodle --------
@wellness_bp.route("/wellness/doodle/new", methods=["GET", "POST"], endpoint="wellness_doodle_new")
@login_required
@limiter.limit("15 per hour")
@trace_route("wellness.wellness_doodle_new")
def doodle_new():
    form = DoodleUploadForm()
    if form.validate_on_submit():
        data_url = form.image_data.data or ""
        # Crisis check not needed for image data; still fail-safe on text later.
        ok, rel_path, err = _save_image_from_data_url(data_url)
        if not ok:
            flash(err, "danger")
            return render_template("wellness/doodle_new.html", form=form)

        # Read raw bytes for vision call
        import os
        abs_path = os.path.join(current_app.static_folder, rel_path)
        try:
            with open(abs_path, "rb") as f:
                img_bytes = f.read()
        except Exception:
            flash("Could not open the saved image.", "danger")
            return render_template("wellness/doodle_new.html", form=form)

        # Vision describe (empathetic)
        interpretation = vision_describe_image(img_bytes, current_user.language_pref or "en")
        # Save Doodle record
        doodle = Doodle(
            user_id=current_user.id,
            image_path=rel_path,
            ai_interpretation=interpretation[:2000],
        )
        db.session.add(doodle)
        db.session.commit()

        # Add a soft EmotionSnapshot (source='doodle'); naive label from text
        label = _infer_label_from_text(interpretation)
        snap = EmotionSnapshot(
            user_id=current_user.id,
            source="doodle",
            score_map=json.dumps({label: 0.7}),
            label=label,
            created_at=datetime.utcnow(),
        )
        db.session.add(snap)
        db.session.commit()

        flash("Saved your doodle 🎨", "success")
        return redirect(url_for("wellness.doodle_detail", doodle_id=doodle.id))

    return render_template("wellness/doodle_new.html", form=form)


@wellness_bp.route("/wellness/doodle/<int:doodle_id>", methods=["GET"], endpoint="wellness_doodle_detail")
@login_required
@trace_route("wellness.doodle_detail")
def doodle_detail(doodle_id: int):
    doodle = Doodle.query.filter_by(id=doodle_id, user_id=current_user.id).first_or_404()
    return render_template("wellness/doodle_detail.html", doodle=doodle)


# -------- Routes: Cultural Story --------
@wellness_bp.route("/wellness/story", methods=["GET", "POST"], endpoint="wellness_story")
@login_required
@limiter.limit("20 per hour")
@trace_route("wellness.static")
def story():
    form = StoryForm()
    story_obj = None
    if form.validate_on_submit():
        theme = form.theme.data
        # Crisis check on theme (unlikely, but consistent)
        crisis = check_crisis_paths(theme or "")
        if crisis.triggered:
            ev = SafetyEvent(user_id=current_user.id, event_type="rate_limit", event_details=json.dumps({"source": "story"}))
            db.session.add(ev)
            db.session.commit()
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        story_obj = generate_cultural_story(theme, current_user.language_pref or "en")
        if request.form.get("action") == "save" and story_obj:
            m = StoryModel(
                user_id=current_user.id,
                theme=theme,
                language=story_obj.language or (current_user.language_pref or "en"),
                story_text=f"{story_obj.title}\n\nMoral: {story_obj.moral}",
            )
            db.session.add(m)
            db.session.commit()
            flash("Story saved 📖", "success")
    return render_template("wellness/story.html", form=form, story=story_obj)


# -------- Routes: Resilience Prompts --------
@wellness_bp.route("/wellness/prompts", methods=["GET", "POST"], endpoint="wellness_prompts")
@login_required
@limiter.limit("30 per hour")
@trace_route("wellness.wellness_prompts")
def prompts():
    form = ResilienceContextForm()
    prompts_list: List[str] | None = None
    if form.validate_on_submit():
        context = (form.context.data or "").strip()
        # Safety check
        crisis = check_crisis_paths(context)
        if crisis.triggered:
            ev = SafetyEvent(user_id=current_user.id, event_type="self_harm_detected", event_details=json.dumps({"source": "prompts", "len": len(context)}))
            db.session.add(ev)
            db.session.commit()
            return render_template("journal/_partials/_grounding_modal.html", show_as_page=True)

        res = create_resilience_prompts(context, current_user.language_pref or "en")
        prompts_list = res.prompts

    # Save single prompt
    if request.method == "POST" and request.form.get("save_prompt"):
        text = (request.form.get("prompt_text") or "").strip()[:1000]
        if text:
            rp = ResiliencePrompt(user_id=current_user.id, prompt_text=text)
            db.session.add(rp)
            db.session.commit()
            flash("Prompt saved 💡", "success")
        return redirect(url_for("wellness.wellness_prompts"))

    return render_template("wellness/prompts.html", form=form, prompts_list=prompts_list)
