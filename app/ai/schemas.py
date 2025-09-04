from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator, ConfigDict

def _clean_schema(schema: dict, *, in_properties: bool = False) -> dict:
    """
    Cleans Pydantic/JSON schema for Gemini models.
    Keeps only fields supported by Gemini (type, properties, items, required).
    Special handling for 'scores' object and nested refs.
    """
    if isinstance(schema, dict):
        cleaned = {}
        for k, v in schema.items():
            # Strip unsupported fields globally
            if k in (
                "title", "description", "$schema",
                "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                "default", "examples", "additionalProperties",
                "$defs", "$ref"
            ):
                continue

            if k == "properties":
                props = {}
                for prop_name, prop_schema in v.items():
                    props[prop_name] = _clean_schema(prop_schema, in_properties=True)

                    # Special case: scores object must declare fixed properties
                    if prop_name == "scores" and props[prop_name].get("type") == "object":
                        allowed_emotions = [
                            "calm", "anxious", "sad", "angry",
                            "hopeful", "tired", "stressed", "motivated"
                        ]
                        props[prop_name]["properties"] = {
                            emo: {"type": "number"} for emo in allowed_emotions
                        }
                cleaned["properties"] = props

            elif k == "items":
                cleaned[k] = _clean_schema(v, in_properties=True)

            elif k == "required":
                # Ensure required list only includes keys that exist in properties
                props = schema.get("properties", {})
                cleaned[k] = [r for r in v if r in props]

            else:
                cleaned[k] = _clean_schema(v, in_properties=in_properties)

        return cleaned

    elif isinstance(schema, list):
        return [_clean_schema(v, in_properties=in_properties) for v in schema]

    return schema

class EmotionAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    primary_label: str = Field(..., description="Primary emotion label")
    scores: Dict[str, float] = Field(default_factory=dict, description="Emotion score map 0..1")
    keywords: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.7)
    explanations: List[str] = Field(default_factory=list)

    @field_validator("scores")
    @classmethod
    def clamp_scores(cls, v: Dict[str, float]):
        return {k: max(0.0, min(1.0, float(x))) for k, x in v.items()}

    @staticmethod
    def as_schema() -> dict:
        raw = EmotionAnalysis.model_json_schema()
        return _clean_schema(raw)


class JournalSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str
    actionable_suggestions: List[str] = Field(default_factory=list)
    detected_emotions: List[str] = Field(default_factory=list)
    tone: str = "supportive"

    @staticmethod
    def as_schema() -> dict:
        raw = JournalSummary.model_json_schema()
        return _clean_schema(raw)


class MeditationPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    duration_sec: int = Field(ge=60, le=1800)
    steps: List[str]

    @staticmethod
    def as_schema() -> dict:
        raw = MeditationPlan.model_json_schema()
        return _clean_schema(raw)


class CulturalStory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    story: str
    moral: str
    language: str

    @staticmethod
    def as_schema() -> dict:
        raw = CulturalStory.model_json_schema()
        return _clean_schema(raw)


class ResiliencePrompts(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompts: List[str]

    @staticmethod
    def as_schema() -> dict:
        raw = ResiliencePrompts.model_json_schema()
        return _clean_schema(raw)


class QAAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    answer: str
    reading_grade: str
    language: str
    references: List[str] = Field(default_factory=list)

    @staticmethod
    def as_schema() -> dict:
        raw = QAAnswer.model_json_schema()
        return _clean_schema(raw)


class PeerModeration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    safe: bool
    reason: str
    suggested_rewrite: Optional[str] = None

    @staticmethod
    def as_schema() -> dict:
        raw = PeerModeration.model_json_schema()
        return _clean_schema(raw)


class CrisisSignal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    triggered: bool
    category: Optional[str] = None
    confidence: float = 0.0

    @staticmethod
    def as_schema() -> dict:
        raw = CrisisSignal.model_json_schema()
        return _clean_schema(raw)


# Optional helper schemas for Step 8+ (art/comics)
class ComicPanel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    panel_caption: str
    dialogue: str
    visual_style: str


class ComicScript(BaseModel):
    model_config = ConfigDict(extra="ignore")
    panels: List[ComicPanel]

    @staticmethod
    def as_schema() -> dict:
        raw = ComicScript.model_json_schema()
        return _clean_schema(raw)


ALLOWED_JOURNAL_EMOTIONS = {"calm","anxious","sad","angry","hopeful","tired","stressed","motivated"}


class JournalInsightsUnified(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str
    actionable_suggestions: List[str] = Field(default_factory=list)
    detected_emotions: List[str] = Field(default_factory=list)
    tone: str = "supportive"
    primary_label: str = ""
    scores: Dict[str, float] = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    explanations: List[str] = Field(default_factory=list)

    @field_validator("scores")
    @classmethod
    def _clamp_scores(cls, v: Dict[str, float]):
        cleaned: Dict[str, float] = {}
        for k, val in (v or {}).items():
            try:
                fv = float(val)
            except Exception:
                continue
            cleaned[k] = max(0.0, min(1.0, fv))
        return cleaned

    @staticmethod
    def as_schema() -> dict:
        raw = JournalInsightsUnified.model_json_schema()
        return _clean_schema(raw)

def normalize_insights(i: JournalInsightsUnified) -> JournalInsightsUnified:
    """Normalization per acceptance criteria (no invention of new data)."""
    # Lowercase & filter emotions
    det: List[str] = []
    for e in i.detected_emotions or []:
        if not e:
            continue
        low = e.strip().lower()
        if low in ALLOWED_JOURNAL_EMOTIONS and low not in det:
            det.append(low)
    # Primary label
    prim = (i.primary_label or "").strip().lower()
    if prim not in ALLOWED_JOURNAL_EMOTIONS:
        prim = det[0] if det else ""
    # Clamp scores & keep only allowed emotion keys
    cleaned_scores: Dict[str, float] = {}
    for k, v in (i.scores or {}).items():
        kk = k.strip().lower()
        if kk not in ALLOWED_JOURNAL_EMOTIONS:
            continue
        try:
            fv = float(v)
        except Exception:
            continue
        cleaned_scores[kk] = max(0.0, min(1.0, fv))
    if prim and prim not in cleaned_scores:
        cleaned_scores[prim] = 0.7
    # Keywords 3-8 constraint (do NOT invent)
    kws = [k.strip() for k in (i.keywords or []) if k and k.strip()]
    if len(kws) > 8:
        kws = kws[:8]
    # If <3 we keep as-is (spec: "if fewer but present, keep as-is; do not invent")
    return JournalInsightsUnified(
        summary=i.summary.strip(),
        actionable_suggestions=[s.strip() for s in (i.actionable_suggestions or []) if s and s.strip()],
        detected_emotions=det,
        tone="supportive",
        primary_label=prim,
        scores=cleaned_scores,
        keywords=kws,
        confidence=max(0.0, min(1.0, float(i.confidence or 0.0))),
        explanations=[x.strip() for x in (i.explanations or []) if x and x.strip()][:2],
    )


def to_summary_and_emotions(i: JournalInsightsUnified) -> Tuple[JournalSummary, EmotionAnalysis]:
    js = JournalSummary(
        summary=i.summary,
        actionable_suggestions=i.actionable_suggestions,
        detected_emotions=i.detected_emotions,
        tone=i.tone,
    )
    ea = EmotionAnalysis(
        primary_label=i.primary_label or (i.detected_emotions[0] if i.detected_emotions else ""),
        scores=i.scores,
        keywords=i.keywords,
        confidence=i.confidence,
        explanations=i.explanations,
    )
    return js, ea


# Backwards compatibility (if older code imports normalize_emotions)
def normalize_emotions(i: JournalInsightsUnified, _source_text: str | None = None) -> JournalInsightsUnified:  # pragma: no cover
    return normalize_insights(i)
