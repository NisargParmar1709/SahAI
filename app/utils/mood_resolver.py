from __future__ import annotations
from typing import Optional
from flask_login import current_user
from sqlalchemy import desc
from app.model import EmotionSnapshot


def latest_detected_mood_for_current_user() -> Optional[str]:
    """Return most recent EmotionSnapshot.label for current user or None.

    Never returns a fabricated fallback. If user not authenticated or no snapshot,
    returns None.
    """
    try:
        if not current_user.is_authenticated:  # type: ignore[attr-defined]
            return None
    except Exception:  # pragma: no cover
        return None
    snap = (
        EmotionSnapshot.query
        .filter_by(user_id=current_user.id)
        .order_by(desc(EmotionSnapshot.created_at))
        .first()
    )
    if not snap or not snap.label:
        return None
    lab = snap.label.strip().lower()
    return lab or None
