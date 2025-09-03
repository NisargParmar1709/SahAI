from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length


class NewJournalForm(FlaskForm):
    """Create a new journal entry. Raw storage is optional (privacy-by-default)."""
    text = TextAreaField(
        "Your journal",
        validators=[
            DataRequired(message="Please share a few lines."),
            Length(max=2000, message="Please keep it under 2000 characters."),
        ],
        render_kw={"rows": 8, "placeholder": "Share how you’re feeling today…"},
    )
    store_raw = BooleanField("Store my raw entry (optional)", default=False)
    submit = SubmitField("Save Entry")
