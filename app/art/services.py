from __future__ import annotations
import os
import secrets
import base64
from typing import Tuple
from flask import current_app

# tiny 1x1 PNG base64 tinted pastel; we render bigger canvas on UI, but file persists safely
# This is a 240x160 pale gradient-like placeholder (pre-encoded). Keeping small for repo.
_PNG_PLACEHOLDER = (
    b"iVBORw0KGgoAAAANSUhEUgAAAPAAAAA+CAYAAAB0y0XzAAAACXBIWXMAAAsSAAALEgHS3X78AAAB"
    b"Y0lEQVR4nO3RAQ0AAAjAMP1/2h0gCQNwqg5z8wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAB0M3aUAAG0C2s0AAAAAElFTkSuQmCC"
)

def _save_png_placeholder(prefix: str = "art") -> str:
    """Save a tiny PNG placeholder to /static/uploads with a random name, return relative path."""
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    name = f"{prefix}_{secrets.token_hex(6)}.jpg"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
    with open(path, "wb") as f:
        f.write(base64.b64decode(_PNG_PLACEHOLDER))
    return f"uploads/{name}"
