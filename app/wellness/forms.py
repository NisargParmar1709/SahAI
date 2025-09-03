from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class MeditationForm(FlaskForm):
    emotions = HiddenField("emotions")  # comma-separated labels from chips (or auto)
    duration_hint = SelectField(
        "Duration",
        choices=[("180", "3 min"), ("300", "5 min"), ("480", "8 min")],
        default="180",
    )
    submit = SubmitField("Generate Plan")


class DoodleUploadForm(FlaskForm):
    # Client sends a base64 data URL string (PNG). We decode & verify on server.
    image_data = HiddenField("image_data", validators=[DataRequired(message="Please draw something first.")])
    submit = SubmitField("Save & Interpret")


class StoryForm(FlaskForm):
    theme = SelectField(
        "Theme",
        choices=[
            ("hope", "Hope"),
            ("perseverance", "Perseverance"),
            ("exam stress", "Exam Stress"),
            ("friendship", "Friendship"),
            ("self-belief", "Self-belief"),
            ("mindfulness", "Mindfulness"),
        ],
        default="hope",
    )
    submit = SubmitField("Generate Story")


class ResilienceContextForm(FlaskForm):
    context = TextAreaField(
        "Optional context",
        validators=[Optional(), Length(max=400, message="Keep it under 400 characters.")],
        render_kw={"rows": 3, "placeholder": "Optional: add a line of context…"},
    )
    submit = SubmitField("Generate Prompts")
