from __future__ import annotations
import re
import hashlib
from typing import Dict, Tuple
from flask import current_app
from .schemas import CrisisSignal

# Regexes for PII redaction
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b\+?\d[\d\s\-]{7,}\d\b")
URL_RE = re.compile(r"\bhttps?://[^\s]+", re.IGNORECASE)


def _mask(tag: str, idx: int) -> str:
    return f"<<{tag}:{idx}>>"


def redact_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """Mask emails, phones, URLs. Return (masked_text, mapping)."""
    mapping: Dict[str, str] = {}
    def _apply(pattern, label, s):
        i = 0
        def repl(m):
            nonlocal i
            key = _mask(label, i)
            i += 1
            mapping[key] = m.group(0)
            return key
        return pattern.sub(repl, s)

    masked = _apply(EMAIL_RE, "EM", text)
    masked = _apply(PHONE_RE, "PH", masked)
    masked = _apply(URL_RE, "URL", masked)
    return masked, mapping


def restore_pii(text: str, mapping: Dict[str, str]) -> str:
    """Replace masks with originals (rarely needed)."""
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def detect_crisis(text: str) -> CrisisSignal:
    """Heuristic keyword scan; later steps may add model assist."""
    if not text:
        return CrisisSignal(triggered=False, category=None, confidence=0.0)
    low = text.lower()
    for w in current_app.config.get("CRISIS_WORDS", []):
        if w in low:
            return CrisisSignal(triggered=True, category="self_harm", confidence=0.85)
    return CrisisSignal(triggered=False, category=None, confidence=0.0)


def apply_response_safety(text: str) -> str:
    """Scrub unsafe suggestions and add caring note."""
    if not text:
        return ""
    cleaned = text.replace("suicide", "[sensitive]").replace("kill", "[sensitive]")
    cleaned += "\n\nIf you're in immediate danger, please reach out to a trusted adult or local helpline."
    return cleaned


def should_block(response_text: str) -> bool:
    """Simple gate using keywords if safety filters enabled."""
    if not current_app.config.get("ENABLE_SAFETY_FILTERS", True):
        return False
    low = (response_text or "").lower()
    return any(term in low for term in ["how to hurt", "self-harm instructions"])
