from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class AskQuestionForm(FlaskForm):
    language = SelectField(
        "Language",
        choices=[("en", "English"), ("hi", "Hindi"), ("hinglish", "Hinglish")],
        default="en",
    )
    question_text = TextAreaField(
        "Ask anonymously",
        validators=[
            DataRequired(message="Please write your question."),
            Length(max=800, message="Please keep it within 800 characters."),
        ],
        render_kw={"rows": 6, "placeholder": "Share your question about stress, studies, relationships…"},
    )
    submit = SubmitField("Ask Safely")
