"""AI package bootstrap for SahAI.

Expose a singleton-ish client getter so routes/services can import:
    from app.ai.gemini_client import get_ai_client
"""
from __future__ import annotations
from .gemini_client import get_ai_client  # re-export
