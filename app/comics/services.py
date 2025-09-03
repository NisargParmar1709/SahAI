from __future__ import annotations
import json
import os
import secrets
import base64
from typing import List
from flask import current_app

# Reuse the tiny PNG placeholder per panel (offline-safe)
_PANEL_PNG = (
    b"iVBORw0KGgoAAAANSUhEUgAAAPAAAAA+CAYAAAB0y0XzAAAACXBIWXMAAAsSAAALEgHS3X78AAAB"
    b"Y0lEQVR4nO3RAQ0AAAjAMP1/2h0gCQNwqg5z8wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    b"AAAAAAB0M3aUAAG0C2s0AAAAAElFTkSuQmCC"
)

def save_panel_images(count: int = 3) -> List[str]:
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    paths = []
    for _ in range(max(3, min(4, count))):
        name = f"comic_{secrets.token_hex(6)}.png"
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
        with open(path, "wb") as f:
            f.write(base64.b64decode(_PANEL_PNG.replace(b' ', b'')))  # keep size minimal
        paths.append(f"uploads/{name}")
    return paths
