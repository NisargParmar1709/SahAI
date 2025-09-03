"""Centralized prompt templates for SahAI."""
from __future__ import annotations

SYSTEM_STYLE = (
    "You are SahAI, an empathetic mental wellness assistant for Indian youth. "
    "Be supportive, non-judgmental, concise, and culturally aware (Hinglish/Hindi/English). "
    "Do not provide medical diagnosis. If the user shows crisis signals, suggest seeking professional help "
    "and national/local helplines. Keep tone warm and simple."
)

DISCLAIMER = (
    "Note: This is supportive guidance, not medical advice. In emergencies, contact local helplines."
)

# Each prompt expects a JSON result matching a provided schema.

PROMPT_EMOTION_ANALYSIS = """
{disclaimer}
Analyze the emotions in the user's text. Return JSON strictly matching the schema.
Text (language={language}):
---
{content}
---
"""

PROMPT_JOURNAL_SUMMARY = """
{disclaimer}
Summarize the journal entry in 2-3 sentences, list actionable suggestions (1-3), and detect emotions.
Return JSON strictly matching the schema.
Language: {language}
Entry:
---
{content}
---
"""

PROMPT_MEDITATION_PLAN = """
{disclaimer}
Create a brief mini-meditation plan tailored for the user.
Inputs: emotions={emotions}, duration_hint={duration_sec}s, language={language}.
Return JSON strictly matching the schema with a few calm steps.
"""

PROMPT_CULTURAL_STORY = """
{disclaimer}
Write a 1-minute culturally resonant story for Indian youth with a clear moral.
Theme: {theme}
Language: {language}
Return JSON strictly matching the schema.
"""

PROMPT_RESILIENCE_PROMPTS = """
{disclaimer}
Generate 3-5 reflective prompts to build resilience.
Context: {context}
Language: {language}
Return JSON strictly matching the schema.
"""

PROMPT_QA_SIMPLE_LANGUAGE = """
{disclaimer}
Answer the question in simple, empathetic {language}. Keep it concise and practical for students.
Return JSON strictly matching the schema.
Question:
---
{question}
---
"""

PROMPT_PEER_MODERATION = """
Moderate the following short text (<=240 chars) for a positive, safe peer wall. If unsafe, explain briefly.
If safe but could be kinder/clearer, suggest a gentle rewrite.
Return JSON strictly matching the schema.
Text:
---
{text}
---
"""

PROMPT_EXAM_COPILOT_SNACKS = """
{disclaimer}
Create 2-3 concise, practical tips for mode={mode}, duration={duration_min} minutes, language={language}.
Return JSON strictly matching the QA schema (answer with bullet tips).
"""

PROMPT_MUSIC_RATIONALE = """
{disclaimer}
In {language}, explain in 1-2 supportive lines why these playlists fit the mood: {mood}.
Keep it kind, stigma-free.
Return plain text (no JSON).
"""

PROMPT_VISION_DESCRIBE = """
{disclaimer}
Describe this doodle/image empathetically in {language}. Infer emotions if possible (non-diagnostic), and be supportive.
Return a short paragraph (plain text).
"""

PROMPT_ART_ABSTRACT = """
{disclaimer}
Generate ONE concise abstract art prompt (<=25 words) capturing the mood/context below.
Mood/context: {mood}
Language: {language}
Style: supportive, uplifting, Indian cultural subtlety OK. Return ONLY the prompt text (no quotes, no JSON).
"""

PROMPT_COMIC_SCRIPT = """
{disclaimer}
Create a short coping or encouragement comic script (3-4 panels) for the situation:
---
{situation}
---
Each panel JSON object must have: panel_caption, dialogue, visual_style.
Return JSON strictly matching the ComicScript schema (panels array only).
Language: {language}
Tone: hopeful, non-judgmental, simple.
"""

# Lean / fallback variant (smaller instructions to reduce latency on retry)
PROMPT_COMIC_SCRIPT_SHORT = """
{disclaimer}
3 panels only. Situation:
---
{situation}
---
Return JSON ONLY with key panels -> list of 3 objects each having panel_caption, dialogue, visual_style.
Keep dialogue <= 60 chars, supportive, {language}.
"""

# Unified Journal Insights (summary + emotions + keywords + scores)
# Strict key set & emotion vocabulary (acceptance criteria)
PROMPT_JOURNAL_INSIGHTS_UNIFIED = """
{disclaimer}
You are an empathetic assistant. Analyze the student's journal entry for supportive reflection.
Return STRICT JSON ONLY with these keys exactly: summary, actionable_suggestions, detected_emotions, tone, primary_label, scores, keywords, confidence, explanations.
Field requirements:
- summary: 2-3 concise, empathetic sentences (plain text, no quotes)
- actionable_suggestions: 2-4 short supportive tips (phrases)
- detected_emotions: list of emotion labels (lowercase) chosen only from: ["calm","anxious","sad","angry","hopeful","tired","stressed","motivated"]
- tone: always the string "supportive"
- primary_label: one label from the same emotion set above (best overall fit)
- scores: object mapping up to 4 of the above emotions to float values 0..1 (no others)
- keywords: 3-8 short neutral key phrases (no PII, no names, no dates)
- confidence: float 0..1 representing overall confidence in analysis
- explanations: 1-2 very short rationale strings (plain text)
Rules:
1. Return strict JSON only. No markdown, no backticks, no prose outside JSON.
2. Do not add extra keys.
3. Do not output clinical diagnostics.
4. Keep language gentle, stigma-free.

Language: {language}
Entry (may be truncated):
---
{entry}
---
"""

PROMPT_JOURNAL_INSIGHTS_UNIFIED_SHORT = """
{disclaimer}
Return STRICT JSON ONLY: summary, actionable_suggestions, detected_emotions, tone, primary_label, scores, keywords, confidence, explanations.
Emotion labels only from: ["calm","anxious","sad","angry","hopeful","tired","stressed","motivated"].
2-3 sentence empathetic summary. 2-4 actionable suggestions. Up to 4 scores 0..1. 3-8 keywords (no PII). 1-2 explanations. tone="supportive".
Return strict JSON only. No markdown, no backticks, no prose outside JSON.
Language: {language}
Entry:
---
{entry}
---
"""
