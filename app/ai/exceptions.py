from __future__ import annotations


class AIConfigError(RuntimeError):
    """Configuration missing or invalid (e.g., missing/invalid API key). Never opens breaker."""


class AIRateLimitError(RuntimeError):
    """429 rate limit reached. Contributes to breaker opening if consecutive."""


class AITimeoutError(RuntimeError):
    """Request exceeded timeout. Counts toward breaker failure threshold."""


class AISafetyError(RuntimeError):
    """Response violates safety filter or 4xx content issue. Should NOT open breaker."""


class AIUnavailableError(RuntimeError):
    """Circuit breaker open or provider/network unavailable."""


class AIStructuredOutputError(RuntimeError):
    """Model failed to produce required JSON structure (repair attempts exhausted). May count if repeated."""
