from __future__ import annotations
from flask import render_template, request
from flask_login import login_required
from . import demo_bp
from app.utils.tracing import trace_route


_DEMO_STEPS = [
    {"title": "Confidential Journal", "desc": "Write a quick entry → see AI summary & emotions.", "href": "/journal.journal_new"},
    {"title": "Emotion Lens", "desc": "Trends, heatmap, distribution (last 7–30 days).", "href": "/journal.journal_emotion_lens"},
    {"title": "Music Recommender", "desc": "Mood → 2–3 playlists + empathetic rationale.", "href": "/music.music_recommend"},
    {"title": "Mini-Meditation", "desc": "3–8 minute plan, TTS & timer.", "href": "/wellness.wellness_meditation"},
    {"title": "Mood Doodle", "desc": "Draw → vision interpretation + snapshot.", "href": "/wellness.wellness_doodle_new"},
    {"title": "Stories", "desc": "1-minute cultural story with moral.", "href": "/wellness.wellness_story"},
    {"title": "Resilience Prompts", "desc": "3–5 reflection prompts; add to journal.", "href": "/wellness.wellness_prompts"},
    # {"title": "Peer Wall", "desc": "Anonymous supportive notes (no replies; hearts only).", "href": "/peer.static['']"},
    # {"title": "Exam Copilot", "desc": "Just-in-time study tips (focus/breath/break).", "href": "/exam"},
    # {"title": "Future Letters", "desc": "Write → lock → unlock later with reflections.", "href": "/letters"},
    {"title": "Mood-to-Art", "desc": "Abstract art from mood/journal.", "href": "/art.art_gallery"},
    {"title": "AI Comics", "desc": "3–4 panel strip from a situation.", "href": "/comics.comics_new"},
    # {"title": "Gratitude Tree", "desc": "Daily leaf with streaks + golden leaves.", "href": "/gratitude"},
]


@demo_bp.route("/script", methods=["GET"], endpoint="demo_script")
@login_required
@trace_route("demo.demp_script")
def script():
    """Clickable script with clear talking points and 'Open Feature' links."""
    try:
        print("enterd try block...")
        return render_template("demo/script.html", steps=_DEMO_STEPS)
    except Exception as e:
        print("enterd error block...")
        print(e)
        return render_template("demo/script.html", steps=_DEMO_STEPS)


@demo_bp.route("/auto", methods=["GET"], endpoint="demo_auto")
@login_required
@trace_route("demo.demo_auto")
def auto():
    """Auto-advancing carousel demo (10s/slide)."""
    return render_template("demo/auto.html", steps=_DEMO_STEPS)


@demo_bp.route("/screenshot", methods=["GET"], endpoint="demo_screenshot")
@login_required
@trace_route("demo.demo_screenshot")
def screenshot():
    """
    Helper page that loads any app route into a same-origin iframe and lets you export a PNG
    via html2canvas. Use for pitch deck screenshots.
    """
    # Default to journal list for convenience; allow ?path=/art/gallery etc.
    path = request.args.get("path", "/journal")
    return render_template("demo/screenshot.html", steps=_DEMO_STEPS, path=path)

@demo_bp.route("/deck", methods=["GET"], endpoint="demo_deck")
@login_required
@trace_route("demo.demo_deck")
def deck():
    """Slide deck presentation with short pitch bullets."""
    slides = [
        {"title": "Problem", "content": "India’s youth face extreme exam pressure + stigma. Few safe spaces."},
        {"title": "Solution", "content": "SahAI 🌱 — a confidential AI wellness buddy. Private, stigma-free, culturally tuned."},
        {"title": "Demo Highlights", "content": "Journal • Emotion Lens • Music • Meditation • Doodle • Story • Prompts • Peer Wall • Exam Copilot • Future Letters • Mood-to-Art • Comics • Gratitude Tree"},
        {"title": "Tech & Safety", "content": "Flask + Bootstrap. Gemini wrapper with PII redaction + crisis detection. Privacy-first DB."},
        {"title": "Vision", "content": "Partner schools + NGOs • Add languages • Reach millions of youth with gentle ally."},
    ]
    return render_template("demo/deck.html", steps=_DEMO_STEPS, slides=slides)
