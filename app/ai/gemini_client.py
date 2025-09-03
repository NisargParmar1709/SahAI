from __future__ import annotations
import json
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
import google.generativeai as genai

from flask import current_app

from .exceptions import (
    AIConfigError, AIRateLimitError, AITimeoutError, AIUnavailableError, AIStructuredOutputError, AISafetyError
)
from .schemas import (
    EmotionAnalysis, JournalSummary, MeditationPlan, CulturalStory as StorySchema,
    ResiliencePrompts as PromptsSchema, QAAnswer, PeerModeration, CrisisSignal, ComicScript,
    JournalInsightsUnified, normalize_insights
)
from . import safety
from .prompt_library import (
    SYSTEM_STYLE, DISCLAIMER, PROMPT_EMOTION_ANALYSIS, PROMPT_JOURNAL_SUMMARY, PROMPT_MEDITATION_PLAN,
    PROMPT_CULTURAL_STORY, PROMPT_RESILIENCE_PROMPTS, PROMPT_QA_SIMPLE_LANGUAGE, PROMPT_PEER_MODERATION,
    PROMPT_EXAM_COPILOT_SNACKS, PROMPT_MUSIC_RATIONALE, PROMPT_VISION_DESCRIBE, PROMPT_ART_ABSTRACT,
    PROMPT_COMIC_SCRIPT, PROMPT_COMIC_SCRIPT_SHORT
)

from app.logging_config import log_extra_safe
import json
logger = logging.getLogger("sahai.ai")


@dataclass
class _BreakerState:
    failures: int = 0
    state: str = "closed"  # closed|open|half_open
    next_try_at: float = 0.0
    last_log_at: float = 0.0
    cooldown_s: int = 0
    half_open_token: bool = True  # only one probe allowed


class _CircuitBreakerRegistry:
    def __init__(self):
        self._states: Dict[str, _BreakerState] = {}

    def _get(self, key: str) -> _BreakerState:
        st = self._states.get(key)
        if not st:
            st = _BreakerState()
            self._states[key] = st
        return st

    def allow(self, key: str, *, log_rate_limit_s: int) -> bool:
        st = self._get(key)
        now = time.time()
        if st.state == "closed":
            return True
        if st.state == "open":
            if now >= st.next_try_at:
                # transition to half-open
                st.state = "half_open"
                st.half_open_token = True
                return True
            # deny; rate-limited log
            if now - st.last_log_at > log_rate_limit_s:
                log_extra_safe(logger, "warning", "ai_breaker_open", extra={"key": key, "cooldown_s": int(st.next_try_at - now)})
                st.last_log_at = now
            return False
        if st.state == "half_open":
            if st.half_open_token:
                st.half_open_token = False
                return True
            return False
        return True

    def record_success(self, key: str):
        st = self._get(key)
        st.failures = 0
        st.state = "closed"
        st.next_try_at = 0.0
        st.cooldown_s = 0
        st.half_open_token = True

    def record_failure(self, key: str, *, reason: str, cfg: Any):
        st = self._get(key)
        qualifying = {"timeout", "rate_limit", "server_error", "network"}
        if reason not in qualifying:
            # Non-qualifying failures do not increment breaker counters; still leave state as-is.
            return
        st.failures += 1
        thresh = cfg.get("AI_BREAKER_FAILURE_THRESHOLD", 3)
        base_cd = cfg.get("AI_BREAKER_BASE_COOLDOWN_S", 30)
        max_cd = cfg.get("AI_BREAKER_MAX_COOLDOWN_S", 120)
        log_rl = cfg.get("AI_LOG_RATE_LIMIT_S", 60)
        now = time.time()
        if st.state == "half_open":
            # failed qualifying probe -> exponential backoff increase
            st.cooldown_s = min(max_cd, max(base_cd, (st.cooldown_s or base_cd) * 2))
            st.state = "open"
            st.next_try_at = now + st.cooldown_s + random.randint(0, 5)
            if now - st.last_log_at > log_rl:
                log_extra_safe(logger, "warning", "ai_breaker_reopen", extra={"key": key, "reason": reason, "cooldown_s": st.cooldown_s})
                st.last_log_at = now
            return
        if st.failures >= thresh and st.state != "open":
            # initial open
            st.cooldown_s = min(max_cd, base_cd + random.randint(0, (max_cd - base_cd)))
            st.state = "open"
            st.next_try_at = now + st.cooldown_s
            if now - st.last_log_at > log_rl:
                log_extra_safe(logger, "warning", "ai_breaker_open", extra={"key": key, "reason": reason, "cooldown_s": st.cooldown_s})
                st.last_log_at = now

    def cooldown_left(self, key: str) -> int:
        st = self._get(key)
        if st.state != "open":
            return 0
        import time as _t
        return max(0, int(st.next_try_at - _t.time()))

    def reset(self, key: str) -> None:
        st = self._get(key)
        st.failures = 0
        st.state = "closed"
        st.next_try_at = 0.0
        st.cooldown_s = 0
        st.half_open_token = True
        
_breaker_registry = _CircuitBreakerRegistry()


class GeminiClient:
    """Robust Gemini wrapper with redaction, retries and structured output.

    Missing/invalid API key raises AIConfigError (callers surface the error; no synthetic content is generated).
    """

    def __init__(self):
        self.api_key = current_app.config.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise AIConfigError("GEMINI_API_KEY not configured.")
        self.text_model_name = current_app.config.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
        self.vision_model_name = current_app.config.get("GEMINI_VISION_MODEL", "gemini-1.5-pro-vision")
        self.timeout = int(current_app.config.get("AI_REQUEST_TIMEOUT", 60))
        self.max_retries = int(current_app.config.get("AI_MAX_RETRIES", 3))
        self.backoff_base = float(current_app.config.get("AI_BACKOFF_BASE", 0.6))
        self.backoff_max = float(current_app.config.get("AI_BACKOFF_MAX", 4.0))
        # Breaker config
        self.brk_threshold = int(current_app.config.get("AI_BREAKER_FAILURE_THRESHOLD", 3))
        self.brk_base_cd = int(current_app.config.get("AI_BREAKER_BASE_COOLDOWN_S", 30))
        self.brk_max_cd = int(current_app.config.get("AI_BREAKER_MAX_COOLDOWN_S", 120))
        self.brk_half_interval = int(current_app.config.get("AI_BREAKER_HALF_OPEN_INTERVAL_S", 10))
        self.log_rate_limit = int(current_app.config.get("AI_LOG_RATE_LIMIT_S", 60))

        self._genai = None
        self._text_model = None
        self._vision_model = None
        self._init_provider()

    def _init_provider(self):
        try:
            import google.generativeai as genai  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise AIConfigError("google-generativeai not installed") from exc

        try:
            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._text_model = genai.GenerativeModel(self.text_model_name)
            self._vision_model = genai.GenerativeModel(self.vision_model_name)
        except Exception as exc:  # pragma: no cover
            raise AIConfigError(f"Failed to initialize Gemini models: {exc}") from exc

    def _with_timeout(self, func, *args, timeout=None, **kwargs):
        """Run func in a thread with a watchdog timeout."""
        join_timeout = timeout or getattr(self, "timeout", 60)
        print(f"[DEBUG:_with_timeout] starting func={getattr(func, '__name__', str(func))}, "
            f"timeout={join_timeout}, args={args}, kwargs={kwargs}")

        result = {"done": False, "value": None, "error": None}

        def target():
            try:
                print(f"[DEBUG:_with_timeout] >>> thread started for {func.__name__}")
                result["value"] = func(*args, **kwargs)
                result["done"] = True
                print(f"[DEBUG:_with_timeout] <<< thread finished successfully for {func.__name__}")
            except Exception as e:
                result["error"] = e
                print(f"[DEBUG:_with_timeout] !!! thread raised exception in {func.__name__}: {e}")

        th = threading.Thread(target=target, daemon=True)
        th.start()
        th.join(join_timeout)

        if not result["done"]:
            print(f"[DEBUG:_with_timeout] TIMED OUT waiting {join_timeout}s for {func.__name__}")
            raise AITimeoutError("AI request timed out")

        if result["error"]:
            print(f"[DEBUG:_with_timeout] ERROR bubbled up from {func.__name__}: {result['error']}")
            raise result["error"]

        print(f"[DEBUG:_with_timeout] returning result from {func.__name__}")
        return result["value"]


    def _call_model(
        self,
        *,
        key: str,
        contents: str,
        json_schema: Optional[dict] = None,
        vision: bool = False,
        timeout_override: Optional[int] = None,
        short_prompt: bool = False
    ) -> Any:
        # Debug: input arguments
        print(f"[DEBUG:_call_model] key={key}, vision={vision}, json_schema={bool(json_schema)}, "
            f"timeout_override={timeout_override}, short_prompt={short_prompt}")

        if not _breaker_registry.allow(key, log_rate_limit_s=self.log_rate_limit):
            cd = _breaker_registry.cooldown_left(key)
            print(f"[DEBUG:_call_model] breaker OPEN for key={key}, cooldown={cd}s")
            raise AIUnavailableError(f"breaker_open:{cd}")

        last_err = None
        client_timeout = timeout_override or getattr(self, "timeout", 60)
        print(f"[DEBUG:_call_model] using client_timeout={client_timeout}")

        for attempt in range(1, self.max_retries + 1):
            start = time.time()
            print(f"[DEBUG:_call_model] attempt={attempt}/{self.max_retries}, key={key}")

            try:
                if vision:
                    raise ValueError("Use dedicated vision call method")

                if json_schema:
                    print(f"[DEBUG:_call_model] calling generate_content with JSON schema...")
                    resp = self._with_timeout(
                        self._text_model.generate_content,
                        contents,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": json_schema,
                        },
                        timeout=client_timeout,
                    )
                    raw = resp.text or "{}"
                    print(f"[DEBUG:_call_model] raw JSON response length={len(raw)}")
                    data = self._parse_json_with_repair(raw, target_schema=json_schema)
                else:
                    print(f"[DEBUG:_call_model] calling generate_content (plain text)...")
                    resp = self._with_timeout(
                        self._text_model.generate_content,
                        contents,
                        timeout=client_timeout,
                    )
                    data = resp.text or ""
                    print(f"[DEBUG:_call_model] plain response length={len(data)}")

                dur = round(time.time() - start, 3)
                print(f"[DEBUG:_call_model] SUCCESS key={key}, duration={dur}s, attempt={attempt}")
                log_extra_safe(
                    logger, "info", "ai_call_ok",
                    extra={
                        "dur_s": dur,
                        "attempt": attempt,
                        "retries": attempt - 1,
                        "structured": bool(json_schema),
                        "key": key,
                        "short_prompt": short_prompt,
                    }
                )
                _breaker_registry.record_success(key)
                return data

            except Exception as exc:  # pragma: no cover
                last_err = exc
                reason = self._classify_exception(exc)
                print(f"[DEBUG:_call_model] ERROR on attempt={attempt}, key={key}, reason={reason}, exc={exc}")

                if reason == "config":
                    raise AIConfigError(str(exc)) from exc
                if reason == "safety":
                    raise AISafetyError(str(exc)) from exc
                if reason == "rate_limit" and attempt == self.max_retries:
                    _breaker_registry.record_failure(key, reason=reason, cfg=current_app.config)
                    log_extra_safe(
                        logger, "warning", "ai_call_fail",
                        extra={"reason": reason, "attempt": attempt, "final": True, "key": key}
                    )
                    raise AIRateLimitError("AI rate limited") from exc

                _breaker_registry.record_failure(key, reason=reason, cfg=current_app.config)
                log_extra_safe(
                    logger, "warning", "ai_call_retry",
                    extra={"reason": reason, "attempt": attempt, "will_retry": attempt < self.max_retries, "key": key}
                )

                sleep_s = min(self.backoff_max, self.backoff_base * (2 ** (attempt - 1))) + random.uniform(0, 0.2)
                print(f"[DEBUG:_call_model] sleeping {sleep_s:.2f}s before retry...")
                time.sleep(sleep_s)

        print(f"[DEBUG:_call_model] FAILED after {self.max_retries} attempts, key={key}, last_err={last_err}")
        raise AIUnavailableError(str(last_err) if last_err else "AI unavailable")


    def _classify_exception(self, exc: Exception) -> str:
        # Attempt to map provider exceptions. Keep generic.
        code = getattr(exc, "status_code", None)
        msg = str(exc).lower()
        if code in (401, 403) or "api key" in msg:
            return "config"
        if code and 400 <= code < 500 and code not in (429, 408):
            # treat 4xx (except rate/timeout) as safety/content issues
            return "safety"
        if code == 429:
            return "rate_limit"
        if isinstance(exc, AITimeoutError):
            return "timeout"
        if code and code >= 500:
            return "server_error"
        if "timeout" in msg:
            return "timeout"
        if any(w in msg for w in ["dns", "network", "connection"]):
            return "network"
        return "unknown"

    # --- JSON repair ---------------------------------------------------------
    def _parse_json_with_repair(self, raw: str, target_schema: Optional[dict]):
        """Attempt to parse JSON; strip fences and repair minor issues.

        We never log raw content (privacy). On failure we raise AIStructuredOutputError.
        """
        from .exceptions import AIStructuredOutputError
        txt = raw.strip()
        # Remove markdown fences / code blocks
        if txt.startswith("```"):
            # Strip code fences (```json ... ```)
            lines = [l for l in txt.splitlines() if not l.strip().startswith("```")]
            txt = "\n".join(lines).strip()
        # Common: model adds leading text before JSON
        first_brace = txt.find("{")
        if first_brace > 0:
            txt = txt[first_brace:]
        # First attempt
        try:
            return json.loads(txt)
        except Exception:
            pass
        # Lightweight repairs
        repaired = txt
        # Remove trailing commas before } or ]
        import re as _re
        repaired = _re.sub(r",\s*(\}|\])", r"\1", repaired)
        # Replace single quotes with double quotes only if double quotes scarce
        if repaired.count('"') < 2 and repaired.count("'") >= 2:
            repaired = repaired.replace("'", '"')
        try:
            return json.loads(repaired)
        except Exception as exc:
            raise AIStructuredOutputError("Could not parse structured JSON output") from exc

    # --- Structured JSON outputs --------------------------------------------
    def analyze_emotions(self, text: str, language: str, *, short_prompt: bool = False) -> EmotionAnalysis:
        masked, _ = safety.redact_pii(text)
        truncated = masked[:800] if short_prompt else masked[:1600]
        prompt = SYSTEM_STYLE + PROMPT_EMOTION_ANALYSIS.format(disclaimer=DISCLAIMER, language=language, content=truncated)
        key = f"{self.text_model_name}:text:analyze_emotions"
        data = self._call_model(key=key, contents=prompt, json_schema=EmotionAnalysis.as_schema(), timeout_override=60, short_prompt=short_prompt)
        try:
            return EmotionAnalysis.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid EmotionAnalysis: {e}")

    def summarize_journal(self, text: str, language: str, store_raw: bool, *, short_prompt: bool = False) -> JournalSummary:
        masked, _ = safety.redact_pii(text)
        truncated = masked[:800] if short_prompt else masked[:1600]
        prompt = SYSTEM_STYLE + PROMPT_JOURNAL_SUMMARY.format(disclaimer=DISCLAIMER, language=language, content=truncated)
        key = f"{self.text_model_name}:text:summarize_journal"
        data = self._call_model(key=key, contents=prompt, json_schema=JournalSummary.as_schema(), timeout_override=60, short_prompt=short_prompt)
        try:
            return JournalSummary.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid JournalSummary: {e}")

    # Unified insights (single structured call). No synthetic fallback here.
    def journal_insights_unified(self, text: str, language: str, *, timeout_override: int = 60, short_prompt: bool = False) -> JournalInsightsUnified:
        from .prompt_library import PROMPT_JOURNAL_INSIGHTS_UNIFIED, PROMPT_JOURNAL_INSIGHTS_UNIFIED_SHORT
        masked, _ = safety.redact_pii(text)
        truncated = masked[:1500]
        tmpl = PROMPT_JOURNAL_INSIGHTS_UNIFIED_SHORT if short_prompt else PROMPT_JOURNAL_INSIGHTS_UNIFIED
        prompt = tmpl.format(disclaimer=DISCLAIMER, language=language, entry=truncated)
        key = f"{self.text_model_name}:text:journal_insights_unified"
        data = self._call_model(
            key=key,
            contents=prompt,
            json_schema=JournalInsightsUnified.as_schema(),
            timeout_override=timeout_override,
            short_prompt=short_prompt,
        )
        try:
            model_obj = JournalInsightsUnified.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid JournalInsightsUnified: {e}")
        # Light normalization (no invention)
        return normalize_insights(model_obj)

    def generate_meditation(self, emotions: list[str], duration_hint: int, language: str) -> MeditationPlan:
        prompt = SYSTEM_STYLE + PROMPT_MEDITATION_PLAN.format(
            disclaimer=DISCLAIMER, emotions=emotions, duration_sec=duration_hint, language=language
        )
        key = f"{self.text_model_name}:text:generate_meditation"
        data = self._call_model(key=key, contents=prompt, json_schema=MeditationPlan.as_schema())
        try:
            return MeditationPlan.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid MeditationPlan: {e}")

    def tell_cultural_story(self, theme: str, language: str) -> StorySchema:
        prompt = SYSTEM_STYLE + PROMPT_CULTURAL_STORY.format(disclaimer=DISCLAIMER, theme=theme, language=language)
        key = f"{self.text_model_name}:text:tell_cultural_story"
        data = self._call_model(key=key, contents=json.dumps(prompt), json_schema=StorySchema.as_schema())
        try:
            return StorySchema.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid CulturalStory: {e}")

    def make_resilience_prompts(self, context: str, language: str) -> PromptsSchema:
        masked, _ = safety.redact_pii(context or "")
        prompt = SYSTEM_STYLE + PROMPT_RESILIENCE_PROMPTS.format(disclaimer=DISCLAIMER, context=masked, language=language)
        key = f"{self.text_model_name}:text:make_resilience_prompts"
        data = self._call_model(key=key, contents=prompt, json_schema=PromptsSchema.as_schema())
        try:
            return PromptsSchema.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid ResiliencePrompts: {e}")

    def answer_question_simple(self, question: str, language: str) -> QAAnswer:
        masked, _ = safety.redact_pii(question)
        prompt = SYSTEM_STYLE + PROMPT_QA_SIMPLE_LANGUAGE.format(disclaimer=DISCLAIMER, language=language, question=masked)
        key = f"{self.text_model_name}:text:answer_question_simple"
        data = self._call_model(key=key, contents=prompt, json_schema=QAAnswer.as_schema())
        try:
            return QAAnswer.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid QAAnswer: {e}")

    def moderate_peer_post(self, text: str, language: str) -> PeerModeration:
        masked, _ = safety.redact_pii(text)
        prompt = PROMPT_PEER_MODERATION.format(text=masked)
        key = f"{self.text_model_name}:text:moderate_peer_post"
        data = self._call_model(key=key, contents=prompt, json_schema=PeerModeration.as_schema())
        try:
            return PeerModeration.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid PeerModeration: {e}")

    def exam_snack(self, mode: str, duration_min: int, language: str) -> QAAnswer:
        prompt = SYSTEM_STYLE + PROMPT_EXAM_COPILOT_SNACKS.format(disclaimer=DISCLAIMER, mode=mode, duration_min=duration_min, language=language)
        key = f"{self.text_model_name}:text:exam_snack"
        data = self._call_model(key=key, contents=prompt, json_schema=QAAnswer.as_schema())
        try:
            return QAAnswer.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid QAAnswer (exam): {e}")

    def generate_comic_script(self, situation: str, language: str, *, short_prompt: bool = False) -> ComicScript:
        masked, _ = safety.redact_pii(situation)
        tmpl = PROMPT_COMIC_SCRIPT_SHORT if short_prompt else PROMPT_COMIC_SCRIPT
        prompt = SYSTEM_STYLE + tmpl.format(disclaimer=DISCLAIMER, situation=masked, language=language)
        key = f"{self.text_model_name}:text:generate_comic_script"
        data = self._call_model(key=key, contents=prompt, json_schema=ComicScript.as_schema(), short_prompt=short_prompt)
        try:
            return ComicScript.model_validate(data)
        except Exception as e:
            raise AIStructuredOutputError(f"Invalid ComicScript: {e}")

    # --- Plain text outputs --------------------------------------------------
    def music_rationale(self, mood: str, language: str) -> str:
        if not mood:
            raise ValueError("mood required")
        prompt = SYSTEM_STYLE + PROMPT_MUSIC_RATIONALE.format(disclaimer=DISCLAIMER, language=language, mood=mood)
        key = f"{self.text_model_name}:text:music_rationale"
        data = self._call_model(key=key, contents=prompt)
        txt = safety.apply_response_safety(str(data).strip())
        return txt

    def generate_art_prompt(self, mood: str, language: str) -> str:
        if not mood:
            raise ValueError("mood required")
        prompt = SYSTEM_STYLE + PROMPT_ART_ABSTRACT.format(disclaimer=DISCLAIMER, mood=mood, language=language)
        key = f"{self.text_model_name}:text:generate_art_prompt"
        data = self._call_model(key=key, contents=prompt)
        return str(data).strip().replace("\n", " ")[:200]

    def vision_describe_image(self, image_bytes: bytes, language: str) -> str:
        try:
            # Build the text instruction prompt
            prompt = SYSTEM_STYLE + PROMPT_VISION_DESCRIBE.format(
                disclaimer=DISCLAIMER,
                language=language
            )

            # Call Gemini vision model directly with image + prompt
            resp = self._with_timeout(
                self._vision_model.generate_content,
                [
                    {"mime_type": "image/png", "data": image_bytes},
                    prompt
                ]
            )

            txt = str(resp.text or "").strip()
            return safety.apply_response_safety(txt)

        except Exception as exc:  # pragma: no cover
            logger.error("vision_describe_error", exc_info=False)
            raise AIUnavailableError(f"Vision describe failed: {exc}")


    # --- Heuristic crisis detection -----------------------------------------
    def detect_crisis_ai(self, text: str) -> CrisisSignal:
        return safety.detect_crisis(text)

    # --- Health -------------------------------------------------------------
    def health_probe(self) -> dict:
        """Non-invasive status probe (no user text)."""
        try:
            # We do not call the model (cost & latency); rely on breaker state & config presence.
            ok = bool(self.api_key) and self._text_model is not None
            return {
                "ok": ok,
                "meta": {
                    "text_model": self.text_model_name,
                    "timeout_s": self.timeout,
                    "retries": self.max_retries,
                },
            }
        except Exception:  # pragma: no cover
            return {"ok": False, "meta": {}}


_client_singleton: Optional[GeminiClient] = None


def get_ai_client() -> GeminiClient:
    global _client_singleton

    if _client_singleton is None:
        _client_singleton = GeminiClient()
    return _client_singleton
