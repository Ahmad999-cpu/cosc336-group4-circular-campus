"""The common AI result envelope (Section 9.1)."""
from dataclasses import dataclass, field
from typing import Any

from .models import AIOutcome


@dataclass
class AIResult:
    """Common envelope from Section 9.1."""

    status: str
    value: Any = None
    confidence: float | None = None
    explanation: str = ""
    model_version_id: Any = None
    inference_id: Any = None
    extra: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in (AIOutcome.OK, AIOutcome.LOW_CONFIDENCE)
