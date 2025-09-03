from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ExamQuestionForm(FlaskForm):
    question = TextAreaField(
        "Ask anything",
        validators=[DataRequired(), Length(min=2, max=400)],
        render_kw={"rows": 2, "placeholder": "Ask about a topic, concept, or practice question…"}
    )
    submit = SubmitField("Ask")
