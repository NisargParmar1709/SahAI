"""SahAI Data Models
Step 3 adds privacy-first wellness entities + relationships.

Privacy principles:
- Default to *not* storing raw text unless explicitly opted-in by the user.
- Prefer summaries/labels; store large blobs on disk and references in DB.
- Soft-delete where relevant via `is_deleted` (no hard removal by default).
- Avoid PII in logs; never store secrets/tokens in these tables.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


# ----------------------------
# Mixins
# ----------------------------
class TimestampMixin:
    """Adds created_at/updated_at columns."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


# ----------------------------
# Core (from Step 1/2)
# ----------------------------
class AppHealth(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(120), nullable=False, default="ok")
    def __repr__(self) -> str:  # pragma: no cover
        return f"<AppHealth id={self.id} note={self.note!r}>"


class User(UserMixin, TimestampMixin, db.Model):
    """SahAI user with privacy-first profile."""
    id = db.Column(db.Integer, primary_key=True)

    # Auth
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    display_name = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.String(500), nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True)
    language_pref = db.Column(db.String(16), nullable=False, default="en")  # 'en','hi','hinglish'

    # Privacy & roles
    consent_analytics = db.Column(db.Boolean, default=False, nullable=False)
    consent_research = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Password reset
    reset_token = db.Column(db.String(255), nullable=True, index=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships (Step 3 backrefs)
    journal_entries = db.relationship("JournalEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    emotion_snapshots = db.relationship("EmotionSnapshot", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    gratitude_entries = db.relationship("GratitudeEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    question_items = db.relationship("QuestionBoxItem", backref="user", lazy="dynamic")
    meditations = db.relationship("MeditationScript", backref="user", lazy="dynamic")
    doodles = db.relationship("Doodle", backref="user", lazy="dynamic")
    cultural_stories = db.relationship("CulturalStory", backref="user", lazy="dynamic")
    resilience_prompts = db.relationship("ResiliencePrompt", backref="user", lazy="dynamic")
    peer_posts = db.relationship("PeerWallPost", backref="user", lazy="dynamic")
    safety_events = db.relationship("SafetyEvent", backref="user", lazy="dynamic")
    future_letters = db.relationship("FutureLetter", backref="user", lazy="dynamic")
    exam_tips = db.relationship("ExamTip", backref="user", lazy="dynamic")
    media_assets = db.relationship("MediaAsset", backref="user", lazy="dynamic")

    # Auth helpers
    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw, method="pbkdf2:sha256")

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    def get_id(self) -> str:  # Flask-Login
        return str(self.id)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r}>"


# ----------------------------
# Wellness Feature Models
# ----------------------------
class JournalEntry(TimestampMixin, db.Model):
    """User journal entry; raw_text optional (privacy-by-default)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    # Privacy-first storage
    raw_text = db.Column(db.Text, nullable=True)            # optional raw
    store_raw = db.Column(db.Boolean, default=False, nullable=False)

    # AI summaries (no PII expected)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_emotions = db.Column(db.Text, nullable=True)         # JSON string: ["anxious","hopeful"]
    ai_keywords = db.Column(db.Text, nullable=True)         # JSON string

    visibility = db.Column(db.String(16), nullable=False, default="private")  # 'private'|'masked'
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.Index("ix_journal_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JournalEntry id={self.id} user={self.user_id}>"


class EmotionSnapshot(db.Model):
    """Lightweight emotion vector snapshot (journal/doodle/question/system)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    source = db.Column(db.String(20), nullable=False)  # 'journal'|'doodle'|'question'|'system'
    score_map = db.Column(db.Text, nullable=True)      # JSON string: {"calm":0.7,"anxious":0.2}
    label = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "created_at", "source", name="uq_emotion_user_time_source"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EmotionSnapshot id={self.id} user={self.user_id} src={self.source}>"


class GratitudeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.Index("ix_gratitude_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<GratitudeEntry id={self.id} user={self.user_id}>"


class QuestionBoxItem(TimestampMixin, db.Model):
    """Anonymous Q&A (user_id nullable)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    ai_answer_text = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(16), nullable=False, default="en")
    status = db.Column(db.String(20), nullable=False, default="submitted")  # 'submitted'|'answered'|'flagged'
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    flag_reason = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuestionBoxItem id={self.id} status={self.status}>"


class MeditationScript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    context_mood = db.Column(db.String(50), nullable=True)
    script_text = db.Column(db.Text, nullable=False)
    duration_sec = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<MeditationScript id={self.id} duration={self.duration_sec}>"


class Doodle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)  # stored under /static/uploads/
    ai_interpretation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Doodle id={self.id} user={self.user_id}>"


class CulturalStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    theme = db.Column(db.String(80), nullable=False)
    language = db.Column(db.String(16), nullable=False, default="en")
    story_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<CulturalStory id={self.id} theme={self.theme!r}>"


class ResiliencePrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    prompt_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_count = db.Column(db.Integer, default=0, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<ResiliencePrompt id={self.id} used={self.used_count}>"


class PeerWallPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    content_text = db.Column(db.String(240), nullable=False)
    ai_moderation_label = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # 'pending'|'published'|'blocked'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    like_count = db.Column(db.Integer, default=0, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<PeerWallPost id={self.id} status={self.status} likes={self.like_count}>"

    @property
    def body(self) -> str:
        return self.content_text

    @body.setter
    def body(self, value: str):
        self.content_text = value

class SafetyEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    event_type = db.Column(db.String(40), nullable=False)  # 'self_harm_detected'|'abuse_detected'|'system_lock'|'rate_limit'
    event_details = db.Column(db.Text, nullable=True)      # short JSON string (no raw user text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<SafetyEvent id={self.id} type={self.event_type}>"


class FutureLetter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    letter_text = db.Column(db.Text, nullable=False)
    open_after = db.Column(db.DateTime, nullable=False)
    is_opened = db.Column(db.Boolean, default=False, nullable=False)
    opened_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    encrypted = db.Column(db.Boolean, default=False, nullable=False)
    encryption_hint = db.Column(db.String(255), nullable=True)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<FutureLetter id={self.id} opened={self.is_opened}>"


class ExamTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)  # nullable for global tips
    tip_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False)  # 'focus'|'breathing'|'motivation'|'break'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExamTip id={self.id} cat={self.category}>"


class MediaAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    kind = db.Column(db.String(30), nullable=False)     # 'abstract_art'|'comic_panel'
    source = db.Column(db.String(20), nullable=False)   # 'ai_generated'|'user_upload'
    file_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    meta_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("ix_media_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MediaAsset id={self.id} kind={self.kind}>"


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self) -> str:  # pragma: no cover
        return f"<AppSetting key={self.key!r}>"
