"""App configuration for SahAI (Supportive AI for Youth Mental Wellness)."""
from __future__ import annotations
import os
from datetime import timedelta
from pathlib import Path


class BaseConfig:
    # Secret & security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///sahai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WTForms CSRF
    WTF_CSRF_TIME_LIMIT = None

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_LOG_JSON = bool(int(os.getenv("DEBUG_LOG_JSON", "1")))
    REQUEST_ID_HEADER = os.getenv("REQUEST_ID_HEADER", "X-Request-ID")
    SQL_ECHO = bool(int(os.getenv("SQL_ECHO", "0")))

    # File uploads (avatars & media)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB
    UPLOAD_EXTENSIONS = {".png", ".jpg", ".jpeg"}
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        str(Path(__file__).resolve().parent / "app" / "static" / "uploads"),
    )

    # Limiter (rate limits)
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "fixed-window"

    # --- AI (Gemini) ---
    # Gemini (production only – external calls). API key MUST be set in environment.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-pro")
    GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash-image-preview")  # unified vision-capable model
    AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "60"))
    AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "3"))
    AI_BACKOFF_BASE = float(os.getenv("AI_BACKOFF_BASE", "0.6"))
    AI_BACKOFF_MAX = float(os.getenv("AI_BACKOFF_MAX", "4.0"))
    # Circuit breaker tuning
    AI_BREAKER_FAILURE_THRESHOLD = int(os.getenv("AI_BREAKER_FAILURE_THRESHOLD", "3"))
    AI_BREAKER_BASE_COOLDOWN_S = int(os.getenv("AI_BREAKER_BASE_COOLDOWN_S", "30"))
    AI_BREAKER_MAX_COOLDOWN_S = int(os.getenv("AI_BREAKER_MAX_COOLDOWN_S", "120"))
    AI_BREAKER_HALF_OPEN_INTERVAL_S = int(os.getenv("AI_BREAKER_HALF_OPEN_INTERVAL_S", "10"))
    AI_LOG_RATE_LIMIT_S = int(os.getenv("AI_LOG_RATE_LIMIT_S", "60"))
    ENABLE_SAFETY_FILTERS = os.getenv("ENABLE_SAFETY_FILTERS", "True").lower() == "true"
    CRISIS_WORDS = [
        # Lightweight, non-exhaustive (kept in code for demo; can be externalized)
        "suicide", "kill myself", "end my life", "hurt myself",
        "self-harm", "cut myself", "i want to die", "no reason to live",
    ]
    timeout = int(os.getenv("AI_TIMEOUT", 60))  # default 60s


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    # Tests still hit Gemini unless GEMINI_API_KEY unset; consider stubbing externally if needed.
