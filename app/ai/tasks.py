from __future__ import annotations
from flask import current_app
from app.logging_config import get_logger, log_extra_safe
_ailog = get_logger("ai.tasks")
from .gemini_client import get_ai_client
from . import safety
from .schemas import (
    EmotionAnalysis, JournalSummary, MeditationPlan, CulturalStory, ResiliencePrompts,
    QAAnswer, PeerModeration, CrisisSignal, ComicScript, JournalInsightsUnified,
    normalize_insights, to_summary_and_emotions
)
from .exceptions import AITimeoutError, AIUnavailableError, AIStructuredOutputError
from typing import Dict, Any, List

MAX_JOURNAL_LEN = 2000
MAX_CONTEXT_LEN = 400
MAX_QUESTION_LEN = 800


def _lang(lang_pref: str) -> str:
    return lang_pref if lang_pref in {"en", "hi", "hinglish"} else "en"


def prepare_journal_insights(text: str, language: str, store_raw: bool) -> tuple[JournalSummary, EmotionAnalysis, List[str]]:
    """Gemini unified journal insights (single call + one retry on limited errors).

    Flow:
    1. Validate length & crisis (crisis handling occurs at route level; we still detect for logging).
    2. First call with full prompt.
    3. On (AITimeoutError | AIUnavailableError | AIStructuredOutputError) only, retry once with short prompt.
    4. On success: normalize + convert to (JournalSummary, EmotionAnalysis, keywords list).
    5. On failure after retry: re-raise last typed exception (no fallback, no invention).
    """

    from .exceptions import AITimeoutError, AIUnavailableError, AIStructuredOutputError

    txt = (text or "").strip()
    if not txt or len(txt) > MAX_JOURNAL_LEN:
        raise ValueError("Journal text invalid length")
    # Crisis detection for logging only (route already handles abort logic)
    crisis_sig = safety.detect_crisis(txt)
    if crisis_sig.triggered:
        log_extra_safe(_ailog, "warning", "journal_crisis_flag", extra={"len": len(txt)})

    client = get_ai_client()
    lang = _lang(language)
    first_exc: Exception | None = None
    unified: JournalInsightsUnified | None = None

    try:
        unified = client.journal_insights_unified(txt, lang, timeout_override=60, short_prompt=False)
    except (AITimeoutError, AIUnavailableError, AIStructuredOutputError) as e:
        first_exc = e
    # Retry with short prompt if eligible
    if unified is None and isinstance(first_exc, (AITimeoutError, AIUnavailableError, AIStructuredOutputError)):
        try:
            unified = client.journal_insights_unified(txt, lang, timeout_override=60, short_prompt=True)
        except (AITimeoutError, AIUnavailableError, AIStructuredOutputError) as e2:
            # bubble up original or second error (choose second for freshest context)
            raise e2
    if unified is None:
        # If we reach here and no exception raised, raise generic unavailable
        from .exceptions import AIUnavailableError
        raise AIUnavailableError("journal insights unavailable")

    normalized = normalize_insights(unified)
    summary, emotions = to_summary_and_emotions(normalized)
    return summary, emotions, (normalized.keywords or [])[:8]


class NoMoodSelectedError(ValueError):
    """Raised when a mood/emotion-dependent feature is invoked without explicit mood(s)."""


def build_meditation_for_user(emotions: List[str], duration_hint: int, language: str) -> MeditationPlan:
    duration_hint = int(duration_hint or 180)
    if duration_hint < 60 or duration_hint > 1800:
        duration_hint = 180
    if not emotions:
        raise NoMoodSelectedError("No emotions provided for meditation generation")
    client = get_ai_client()
    return client.generate_meditation(emotions, duration_hint, _lang(language))


def generate_cultural_story(theme: str, language: str) -> CulturalStory:
    theme = (theme or "hope").strip()[:50]
    client = get_ai_client()
    return client.tell_cultural_story(theme, _lang(language))


def create_resilience_prompts(context: str, language: str) -> ResiliencePrompts:
    context = (context or "").strip()[:MAX_CONTEXT_LEN]
    client = get_ai_client()
    return client.make_resilience_prompts(context, _lang(language))


def answer_user_question(question: str, language: str) -> QAAnswer:
    q = (question or "").strip()
    if not q or len(q) > MAX_QUESTION_LEN:
        raise ValueError("Question too long or empty.")
    client = get_ai_client()
    return client.answer_question_simple(q, _lang(language))


def moderate_and_rewrite_peer_post(text: str, language: str) -> PeerModeration:
    content = (text or "").strip()[:240]
    client = get_ai_client()
    return client.moderate_peer_post(content, _lang(language))


def check_crisis_paths(text: str) -> CrisisSignal:
    return safety.detect_crisis(text or "")


def music_rationale(mood: str | None, language: str) -> str:
    if not mood:
        raise NoMoodSelectedError("Mood required for music rationale")
    m = mood.strip().lower()[:40]
    client = get_ai_client()
    # No fallback text; propagate exceptions
    return client.music_rationale(m, _lang(language))


def exam_snack(mode: str, duration_sec: int, language: str) -> QAAnswer:
    client = get_ai_client()
    return client.exam_snack((mode or "focus"), int(duration_sec / 60), _lang(language))


def vision_describe_image(image_bytes: bytes, language: str) -> str:
    client = get_ai_client()
    return client.vision_describe_image(image_bytes, _lang(language))

def generate_art_prompt(mood_text: str | None, language: str) -> str:
    if not mood_text:
        raise NoMoodSelectedError("Mood required for art prompt generation")
    client = get_ai_client()
    mood = mood_text.strip()[:200]
    return client.generate_art_prompt(mood, _lang(language))

def generate_comic_script(situation: str, language: str) -> Dict[str, Any]:
    """Generate a comic script with one fallback retry using a shorter prompt.

    Strategy mirrors journal insights resilience:
    1. Full prompt attempt.
    2. On timeout / unavailable / structured parse failure -> retry once with short prompt.
    3. Propagate second error if retry fails (no fabrication).
    """
    client = get_ai_client()
    sit = (situation or "Exam stress").strip()[:240]
    first_exc: Exception | None = None
    script: ComicScript | None = None
    try:
        script = client.generate_comic_script(sit, _lang(language), short_prompt=False)
    except (AITimeoutError, AIUnavailableError, AIStructuredOutputError) as e:
        first_exc = e
    if script is None and isinstance(first_exc, (AITimeoutError, AIUnavailableError, AIStructuredOutputError)):
        try:
            script = client.generate_comic_script(sit, _lang(language), short_prompt=True)
        except (AITimeoutError, AIUnavailableError, AIStructuredOutputError) as e2:
            raise e2
    if script is None:
        from .exceptions import AIUnavailableError as _AU
        raise _AU("comic script unavailable")
    return script.model_dump()

def summarize_journal(text: str, language: str, store_raw: bool = False) -> JournalSummary:
    """Thin wrapper used by Letters to generate a reflection summary."""
    txt = (text or "").strip()
    if not txt:
        raise ValueError("Empty journal text.")
    client = get_ai_client()
    return client.summarize_journal(txt, _lang(language), store_raw=store_raw)
