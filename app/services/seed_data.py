"""Idempotent seed data for SahAI demo.

Run via: `flask seed`
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app

from ..extensions import db
from ..model import (
    User, JournalEntry, EmotionSnapshot, GratitudeEntry, CulturalStory,
    ExamTip, PeerWallPost, MeditationScript, MediaAsset, AppSetting, FutureLetter
)
from werkzeug.security import generate_password_hash
import os
import secrets

def _ensure_demo_user() -> User:
    user = User.query.filter_by(username="demo").first()
    if not user:
        user = User(username="demo", email="demo@example.com", language_pref="en")
        user.set_password("demo1234")
        db.session.add(user)
        db.session.commit()
    return user


def _seed_journal_and_emotions(user: User):
    if JournalEntry.query.filter_by(user_id=user.id).count() == 0:
        je1 = JournalEntry(
            user_id=user.id,
            raw_text=None,
            store_raw=False,
            ai_summary="Felt a bit anxious but hopeful after studying.",
            ai_emotions=json.dumps(["anxious", "hopeful"]),
            ai_keywords=json.dumps(["study", "breathing"]),
            visibility="private",
        )
        je2 = JournalEntry(
            user_id=user.id,
            raw_text="I did a short walk today and it helped.",
            store_raw=True,
            ai_summary="Walking improved mood; feeling calmer.",
            ai_emotions=json.dumps(["calm", "hopeful"]),
            ai_keywords=json.dumps(["walk", "calm"]),
            visibility="private",
        )
        db.session.add_all([je1, je2])
        db.session.commit()

        # Emotion snapshots
        snap1 = EmotionSnapshot(
            user_id=user.id,
            source="journal",
            score_map=json.dumps({"calm": 0.3, "anxious": 0.6, "hopeful": 0.5}),
            label="anxious",
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        snap2 = EmotionSnapshot(
            user_id=user.id,
            source="journal",
            score_map=json.dumps({"calm": 0.7, "anxious": 0.2, "hopeful": 0.6}),
            label="calm",
        )
        db.session.add_all([snap1, snap2])
        db.session.commit()


def _seed_gratitude(user: User):
    if GratitudeEntry.query.filter_by(user_id=user.id).count() == 0:
        items = [
            GratitudeEntry(user_id=user.id, content="Parents' support"),
            GratitudeEntry(user_id=user.id, content="A good cup of chai"),
            GratitudeEntry(user_id=user.id, content="Clear sky after rain"),
        ]
        db.session.add_all(items)
        db.session.commit()


def _seed_stories_and_tips(user: User):
    if CulturalStory.query.count() == 0:
        db.session.add_all([
            CulturalStory(user_id=None, theme="perseverance", language="en",
                          story_text="A short tale of keeping faith during exams."),
            CulturalStory(user_id=None, theme="hope", language="hinglish",
                          story_text="Chhoti si kahani ummeed ki."),
        ])
        db.session.commit()

    if ExamTip.query.count() == 0:
        db.session.add_all([
            ExamTip(user_id=None, category="focus", tip_text="Use Pomodoro: 25 min focus + 5 min break."),
            ExamTip(user_id=None, category="breathing", tip_text="Try 4-7-8 breathing for 2 minutes."),
            ExamTip(user_id=None, category="motivation", tip_text="Write one line why you started."),
            ExamTip(user_id=None, category="break", tip_text="Stretch your neck and shoulders."),
        ])
        db.session.commit()


def _seed_peer_and_media(user: User):
    if PeerWallPost.query.count() == 0:
        db.session.add_all([
            PeerWallPost(user_id=None, content_text="You’ve got this! One page at a time 🌱",
                         ai_moderation_label="safe", status="published"),
            PeerWallPost(user_id=None, content_text="Drink water and breathe—proud of you 💙",
                         ai_moderation_label="safe", status="published"),
        ])
    # MediaAsset placeholder
    static_demo = Path(current_app.root_path) / "static" / "img" / "demo_art.jpg"
    static_demo.parent.mkdir(parents=True, exist_ok=True)
    if not static_demo.exists():
        # Tiny 1x1 png placeholder
        static_demo.write_bytes(
            bytes.fromhex(
                "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE0000000A49444154789C6360000002000154A2F2A90000000049454E44AE426082"
            )
        )
    if MediaAsset.query.filter_by(user_id=user.id).count() == 0:
        db.session.add(MediaAsset(
            user_id=user.id, kind="abstract_art", source="ai_generated",
            file_path="static/img/demo_art.jpg", caption="Calm sunrise", meta_json=None
        ))
    db.session.commit()


def _seed_meditation(user: User):
    if MeditationScript.query.filter_by(user_id=user.id).count() == 0:
        db.session.add(MeditationScript(
            user_id=user.id, context_mood="calm",
            script_text="Close your eyes. Breathe in 4, hold 4, out 6...",
            duration_sec=180
        ))
        db.session.commit()


def _seed_settings():
    if not AppSetting.query.filter_by(key="onboarding_message").first():
        db.session.add(AppSetting(key="onboarding_message",
                                  value="Welcome to SahAI! You are safe here. 🌱"))
        db.session.commit()


def seed() -> None:
    """Idempotent seed for demo account/content."""
    user = _ensure_demo_user()
    _seed_journal_and_emotions(user)
    _seed_gratitude(user)
    _seed_stories_and_tips(user)
    _seed_peer_and_media(user)
    _seed_meditation(user)
    _seed_settings()
    current_app.logger.info("Seed complete", extra={"user_id": user.id})

def _ensure_uploads():
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)


def seed() -> None:
    """Idempotent seed for demo account and sample content."""
    _ensure_uploads()

    demo = User.query.filter_by(username="demo").first()
    if not demo:
        demo = User(
            username="demo",
            email="demo@example.com",
            password_hash=generate_password_hash("demo1234"),
            display_name="Demo User",
            language_pref="en",
            is_active=True,
        )
        db.session.add(demo)
        db.session.commit()

    # Gratitude 3 recent
    if GratitudeEntry.query.filter_by(user_id=demo.id).count() == 0:
        for i, text in enumerate([
            "Morning sunlight through the window",
            "A friend who checked in",
            "Understanding a tough concept finally",
        ]):
            ge = GratitudeEntry(user_id=demo.id, content=text, created_at=datetime.utcnow() - timedelta(days=2 - i))
            db.session.add(ge)

    # Journal + Emotion snapshot lite
    if JournalEntry.query.filter_by(user_id=demo.id, is_deleted=False).count() == 0:
        je = JournalEntry(
            user_id=demo.id,
            raw_text=None,
            store_raw=False,
            ai_summary="Felt anxious before exams but practiced breathing; small win today.",
            ai_emotions=json.dumps(["anxious", "hopeful"]),
            ai_keywords=json.dumps(["exam", "breathing", "win"]),
            visibility="private",
        )
        db.session.add(je)
        db.session.flush()
        snap = EmotionSnapshot(
            user_id=demo.id,
            source="journal",
            score_map=json.dumps({"anxious": 0.4, "hopeful": 0.5}),
            label="hopeful",
        )
        db.session.add(snap)

    # Peer posts
    if PeerWallPost.query.filter_by(status="published").count() == 0:
        db.session.add(PeerWallPost(user_id=demo.id, content_text="If today is heavy, take one tiny gentle step. 🌱", status="published", like_count=3))
        db.session.add(PeerWallPost(user_id=demo.id, content_text="Breathe in 4… hold 7… out 8. You’ve got this.", status="published", like_count=5))

    # Exam tips
    if ExamTip.query.count() == 0:
        db.session.add(ExamTip(user_id=None, tip_text="Use Pomodoro: 25-min focus + 5-min stretch.", category="focus"))
        db.session.add(ExamTip(user_id=None, tip_text="4-7-8 breathing before starting a paper.", category="breathing"))

    # Meditation sample
    if MeditationScript.query.filter_by(user_id=demo.id).count() == 0:
        db.session.add(MeditationScript(user_id=demo.id, context_mood="hopeful", script_text="Sit upright; soften shoulders; slow breath; notice; thank yourself.", duration_sec=180))

    # Cultural story
    if CulturalStory.query.filter_by(user_id=None).count() == 0:
        db.session.add(CulturalStory(user_id=None, theme="hope", language="en", story_text="A diya flickers in the wind yet keeps glowing. Moral: Small consistent effort builds resilience."))

    # Future Letter (locked 30 days)
    if FutureLetter.query.filter_by(user_id=demo.id).count() == 0:
        db.session.add(FutureLetter(user_id=demo.id, title="To Future Me", letter_text="Proud of you for showing up. Keep choosing kindness.", open_after=datetime.utcnow()+timedelta(days=30), is_opened=False))

    # App setting
    if not AppSetting.query.filter_by(key="onboarding_message").first():
        db.session.add(AppSetting(key="onboarding_message", value="Welcome to SahAI 🌱"))

    db.session.commit()
