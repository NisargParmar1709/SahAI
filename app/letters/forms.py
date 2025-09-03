from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Length


class LetterForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    letter_text = TextAreaField(
        "Your letter",
        validators=[DataRequired(), Length(max=2000)],
        render_kw={"rows": 10, "placeholder": "Write a kind note to your future self…"}
    )
    open_after = DateField("Open on (YYYY-MM-DD)", validators=[DataRequired()], format="%Y-%m-%d")
    submit = SubmitField("Save Letter")
