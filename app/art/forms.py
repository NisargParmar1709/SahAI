from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField, SubmitField
from wtforms.validators import Optional, Length


class ArtForm(FlaskForm):
    mood_text = TextAreaField(
        "Describe your mood (optional)",
        validators=[Optional(), Length(max=200)],
        render_kw={"rows": 3, "placeholder": "e.g., calm sunrise vibes, hopeful after tough day…"}
    )
    use_last_journal = BooleanField("Use last journal summary")
    submit = SubmitField("Generate Art")
