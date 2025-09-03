from flask.cli import with_appcontext
import click

FULL_SCRIPT = """
[5-Minute Full Pitch]

Problem:
• Indian students face overwhelming exam stress, rising anxiety, stigma.
• Few safe spaces; therapy is costly, public, or judged.

Solution:
• SahAI 🌱 — confidential AI wellness buddy.
• Private-by-default, stigma-free, culturally tuned.

Demo Highlights:
• Journal + AI summary + Emotion Lens
• Music recommender, Mini-Meditation, Doodle
• Stories & Prompts, Peer Wall, Exam Copilot
• Creative outlets: Future Letters, Mood-to-Art, Comics
• Gratitude Tree with streaks

Tech & Safety:
• Flask + Bootstrap + SQLite
• Gemini wrapper with PII redaction, crisis guard, soft delete
• No raw data logs, summary-first storage

Impact:
• Helps youth self-reflect, manage stress, and build resilience
• Accessible in English, Hindi, Hinglish (more languages coming)

Vision:
• Partner with schools & NGOs
• Expand into more languages
• Support millions of youth with stigma-free ally

Team:
• Student founders with lived experience
• Advisors in mental health & education

Ask:
• Pilot with 3 schools / 1000 students
• Support for scaling infra & language packs

Thank you — SahAI 🌱
""".strip()


@click.command("pitch_full")
@with_appcontext
def pitch_full_cmd():
    """Print the extended 5-minute pitch script."""
    click.echo(FULL_SCRIPT)


def register_cli_full(app):
    app.cli.add_command(pitch_full_cmd)
