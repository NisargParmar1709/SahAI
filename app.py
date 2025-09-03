"""Entrypoint for running SahAI with `flask run` or `python app.py`."""
from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env if present

from app import create_app  # noqa: E402

# If FLASK_CONFIG not set, default to Development
config_path = os.getenv("FLASK_CONFIG", "config.DevelopmentConfig")
app = create_app(config_path)

# ---- Auto DB create ---------------------------------------------------------
try:
    # Ensure SQLite folder exists (if using sqlite:///sahai.db)
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "sqlite:///sahai.db")
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "", 1)
        db_dir = os.path.dirname(db_path) or "."
        os.makedirs(db_dir, exist_ok=True)

    # Create all tables if they don't exist yet (non-destructive)
    from app.extensions import db  # local import to avoid circulars
    with app.app_context():
        db.create_all()
        # Optional: you can print once to console
        print("✅ DB ready: tables ensured via create_all()")
except Exception as e:  # pragma: no cover
    print(f"⚠️  DB init warning: {e}")

# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Run without the Flask auto-reloader (web reloader) as requested
    # app.run(debug=True, use_reloader=False)
    app.run(debug=True)