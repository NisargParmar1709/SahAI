from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, Regexp


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField(
        "Email (optional)",
        validators=[Optional(), Email(check_deliverability=False)]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    username_or_email = StringField("Username or Email", validators=[DataRequired(), Length(min=3, max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class ForgotPasswordForm(FlaskForm):
    username_or_email = StringField("Username or Email", validators=[DataRequired(), Length(min=3, max=255)])
    submit = SubmitField("Send reset link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(r".*[A-Za-z].*", message="Include letters."),
            Regexp(r".*[0-9].*", message="Include at least one number."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")]
    )
    submit = SubmitField("Reset password")
