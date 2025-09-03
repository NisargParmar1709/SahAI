from __future__ import annotations
from flask import current_app
from flask.cli import with_appcontext
import click


PITCH_TEXT = """
[3-Minute Pitch Script]

(0:00–0:30) Problem:
India’s youth face intense study pressure, stigma, and limited safe spaces to reflect. Many avoid seeking help because it feels public or judgmental.

(0:30–1:00) Solution:
SahAI is a confidential AI wellness buddy. It’s stigma-free, private by default, and culturally tuned for Indian youth — English, Hindi, Hinglish.

(1:00–2:00) Demo Highlights:
• Confidential Journal → instant supportive summaries + Emotion Lens trends.
• Music Recommender → mood-based playlists with empathetic rationale.
• Mini-Meditation → 3–8 minute plans with TTS + timer.
• Mood Doodle → draw feelings, get a gentle reflection.
• Stories & Prompts → 1-minute cultural stories and reflection prompts.
• Peer Wall → anonymous uplifting notes (no replies; AI moderation).
• Exam Copilot → just-in-time focus/breath/motivation tips.
• Future Letters → write now, unlock later with insights.
• Mood-to-Art & AI Comics → creative outlets with strict safety & privacy.
• Gratitude Tree → one daily leaf, streaks, and golden leaves.

(2:00–2:30) Tech & Safety:
Flask + Bootstrap + SQLite; Gemini (live) wrapper with PII redaction, crisis detection, structured outputs. No raw data logged. Summary-first storage and soft delete.

(2:30–3:00) Vision:
Partner with schools/NGOs, add more Indian languages, and support millions of youth with a gentle, stigma-free ally.

Thank you — SahAI 🌱
""".strip()


@click.command("pitch")
@with_appcontext
def pitch_cmd() -> None:
    """Print a clean 3-minute spoken pitch script."""
    click.echo(PITCH_TEXT)


def register_cli(app):
    app.cli.add_command(pitch_cmd)
