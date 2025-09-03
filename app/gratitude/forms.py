from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class GratitudeForm(FlaskForm):
    content = TextAreaField(
        "What are you grateful for today?",
        validators=[DataRequired(), Length(min=3, max=200)],
        render_kw={
            "rows": 3,
            "placeholder": "One small thing is enough — e.g., a cup of chai, a kind text, a quiet moment…",
            "aria-describedby": "gratitudeHelp",
        },
    )
    submit = SubmitField("Add Leaf")
