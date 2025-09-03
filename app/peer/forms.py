from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class PeerPostForm(FlaskForm):
    body = TextAreaField(
        "Your message",
        validators=[DataRequired(), Length(min=2, max=500)],
        render_kw={"rows": 3, "placeholder": "Write something supportive…"}
    )
    submit = SubmitField("Post")
