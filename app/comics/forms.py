from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ComicForm(FlaskForm):
    situation = TextAreaField(
        "Describe a stressful/funny situation (≤ 200 chars)",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"rows": 3, "placeholder": "e.g., Night before exam, chai spilled on notes…"}
    )
    submit = SubmitField("Create Comic")
