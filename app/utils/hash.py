from __future__ import annotations
import hashlib
from flask_login import current_user

def user_hash() -> str:
    try:
        if current_user.is_authenticated:  # type: ignore[attr-defined]
            return hashlib.sha256(str(current_user.id).encode()).hexdigest()[:12]
    except Exception:
        pass
    return "anon"
