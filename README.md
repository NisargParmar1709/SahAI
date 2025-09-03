# SahAI – Supportive AI for Youth Mental Wellness

Live Gemini-powered Flask web app delivering reflective journaling, mini-meditations, emotion insights, resilience prompts, cultural stories, mood-based music rationale, doodle interpretation, anonymous peer wall moderation, exam focus tips, future letters reflections, mood‑to‑art prompt generation, and comic scripts.

## Key Features (All Backed by Google Gemini)
- Journal summaries + emotion lens (structured JSON)
- Emotion analysis & trend snapshots
- Mini-meditation script generation
- Cultural storytelling (1‑minute moral tales)
- Resilience reflection prompts
- Anonymous Q&A (simple-language answers)
- Peer Wall AI moderation & gentle rewrites
- Exam Copilot snack tips (focus / calm / motivation)
- Future You letters reflection summaries
- Mood doodle vision interpretation (vision model)
- Mood → abstract art prompt (text only)
- Situation → 3–4 panel comic script JSON
- Mood-based music rationale text

## Tech & Safety
- Flask + SQLAlchemy + WTForms + Flask-Limiter
- Google Gemini (text + vision) via `google-generativeai`
- PII redaction before send; safety scrubbing after receive
- Crisis keyword heuristic (configurable `CRISIS_WORDS`)
- Circuit breaker + retries with exponential backoff
- Structured outputs validated with Pydantic schemas
- All features require a valid Gemini key (no offline fallback)

## Quick Start
```bash
pip install -r requirements.txt
# Set environment (PowerShell example)
$env:GEMINI_API_KEY = "your_real_key"
# (Optional) create .env with GEMINI_API_KEY=...
flask db upgrade  # if migrations configured; else create_all runs automatically
flask run
```
Or run directly:
```bash
python app.py
```

## Required Environment Variables
| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | REQUIRED. Obtain from Google AI Studio. |
| `GEMINI_TEXT_MODEL` | (Optional) default `gemini-1.5-pro`. |
| `GEMINI_VISION_MODEL` | (Optional) default `gemini-1.5-pro-vision`. |
| `ENABLE_SAFETY_FILTERS` | Default `True`. |
| `AI_REQUEST_TIMEOUT` | Default `60` (seconds). |
| `AI_BREAKER_FAILURE_THRESHOLD` | Failures before open (default 3). |
| `AI_BREAKER_BASE_COOLDOWN_S` | Base cooldown seconds (default 30). |
| `AI_BREAKER_MAX_COOLDOWN_S` | Max cooldown seconds (default 120). |
| `AI_BREAKER_HALF_OPEN_INTERVAL_S` | Probe interval while half-open (default 10). |
| `AI_LOG_RATE_LIMIT_S` | Min seconds between repeated breaker warnings (default 60). |

Place them in `.env` (loaded via `python-dotenv`) or export in the shell.

Example `.env`:
```
SECRET_KEY=change-me
GEMINI_API_KEY=YOUR_KEY_HERE
GEMINI_TEXT_MODEL=gemini-1.5-pro
GEMINI_VISION_MODEL=gemini-1.5-pro-vision
ENABLE_SAFETY_FILTERS=True
AI_REQUEST_TIMEOUT=60
```

## Architecture Overview
- `app/ai/gemini_client.py` central wrapper (timeouts, retries, schemas, safety)
- `app/ai/tasks.py` task-level convenience functions used by blueprints
- Modular blueprints: `journal`, `wellness`, `music`, `letters`, `art`, `comics`, `exam`, `peer`, etc.
- Pydantic schemas in `app/ai/schemas.py` drive structured JSON with Gemini response schema guidance

## Mood Resolution (No Silent Defaults)
Features that require a mood (music recommendations, meditation, certain art prompts) use your most recent detected emotion (from `EmotionSnapshot`). If none exists yet, the UI prompts you to explicitly choose a mood. The application never silently defaults to a placeholder like "calm".

## Safety & Privacy
- PII (emails/phones/URLs) masked before sending to Gemini
- Post-response safety scrub (keywords → `[sensitive]` + helpline footer)
- Crisis detection prevents storing risky raw text and can divert to grounding UI
- Minimal storage: journal entries store summaries & optionally raw text (configurable in calling code)

## Testing Notes
Tests now require a real key for AI-dependent paths. For isolated unit tests, you can monkeypatch `get_ai_client()` with a stub that returns deterministic Pydantic models.

## Extending
1. Add a new Pydantic schema (if structured) in `schemas.py`.
2. Create a prompt template in `prompt_library.py`.
3. Add a method in `gemini_client.py` calling `_call_model` with schema.
4. Expose through `tasks.py` and a blueprint route.

## Deployment
Ensure `GEMINI_API_KEY` is injected securely (never commit keys). Behind a WSGI server (gunicorn/uwsgi) set `FLASK_CONFIG=config.ProductionConfig`.

## Troubleshooting
Journal entries always save. If Gemini is slow, times out, rate limited, or returns malformed JSON:
- A safe fallback summary is stored (no emotion scores) so your reflection is never lost.
- You’ll see: “Journal saved. AI insights couldn’t be generated right now.”
- System logs only a WARNING with non‑PII metadata (user id, length, language) — no raw text or stacktrace for normal timeouts.
Adaptive retry: first full prompt, then a compact summary/emotion prompt if needed. After two failures we degrade gracefully.

### Circuit Breaker
The AI circuit breaker opens only on infrastructural issues: repeated timeouts, 429 rate limits, network/DNS errors, or 5xx responses. It does NOT open for:
- Configuration problems (401/403) – surfaced as config errors
- Safety / content 4xx rejections – handled gracefully

Behavior:
1. Closed: normal operation.
2. After N (threshold) consecutive qualifying failures per method key (e.g., `gemini-1.5-pro:text:summarize_journal`), it opens with a randomized cooldown between base and max.
3. When cooldown expires, transitions to half-open and allows one probe. Success closes breaker; failure re-opens with exponential cooldown backoff.
4. Logs are rate-limited (`AI_LOG_RATE_LIMIT_S`) to avoid noise.

Fallback Guarantee: Even if open, journal entries still save with a friendly message.

### Journal Insights Reliability
Journal insights now use ONE unified Gemini call returning: summary, actionable suggestions, detected_emotions, primary_label, scores, keywords, confidence, explanations. Validation is performed with Pydantic. Flow:
1. Full prompt attempt (strict JSON enforced by Gemini response schema)
2. On (timeout | unavailable | JSON schema parse error) only, one retry with a short prompt
3. If still failing: the entry is saved (if user opted) WITHOUT any synthetic or fallback AI data; the UI shows a single toast: “AI insights could not be generated. Please try again.”
4. No locally invented summaries, emotions, or keywords – what you see is either real model output (validated) or nothing.

Normalization only lowercases/filters emotion labels, clamps numeric ranges, and truncates keyword lists (never invents new content). This keeps provenance clear and debuggable.

## Diagnostics

Health Probe:
- GET `/_health/ai` → `{ "ok": true/false, "meta": { ... } }` (200 when `ok=true`, else 503). No user data is processed.

Enable Debug Logging (PowerShell):
```powershell
$env:LOG_LEVEL="DEBUG"; $env:FLASK_ENV="development"; flask run
```
Expect verbose structured AI logs: `ai_call_ok`, `ai_call_retry`, `ai_breaker_open`, `journal_ai_fail` (no raw text). Journal analysis path: `journal.routes` → `prepare_journal_insights` (tasks) → `GeminiClient.journal_insights_unified` → template `templates/journal/detail.html`.

Tracing Issues:
- If `journal_ai_fail` appears, check for preceding `ai_call_retry` or breaker messages.
- For JSON issues you should see `ai_call_retry` followed by an `AIStructuredOutputError` warning.
- Use `/ _health / ai` to distinguish model outage vs parsing problems.

Common Failure Causes & Signals:
- Timeout → `AITimeoutError` + retry (short prompt)
- Malformed JSON → `AIStructuredOutputError` + retry
- Circuit breaker open → immediate `AIUnavailableError breaker_open:NN` (no retry)

Zero PII Guarantee in Logs: only lengths, language codes, event types.

## License
Internal hackathon project – add license info if open sourcing.

---
SahAI 🌱 – "Small steps, gentle support."
