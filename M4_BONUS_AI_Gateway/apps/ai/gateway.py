"""AIGateway (ADR-3): the only code that talks to an external AI provider.

Responsibilities: pick the active ModelVersion, strip personal fields, enforce a time limit, normalise
confidence, and write an AIInferenceRecord for every call. Callers always get an AIResult and must handle
every status; nothing here writes to business tables (BR-12).
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import time

from django.conf import settings

from .models import AICapability, AIInferenceRecord, AIOutcome, ModelStatus, ModelVersion
from .providers import get_provider
from .result import AIResult


# Time limits from Table 8.2 (seconds).
TIME_LIMITS = {
    AICapability.CLASSIFY: 5, AICapability.CHAT: 8, AICapability.RECOMMEND: 120,
    AICapability.SUMMARIZE: 120, AICapability.BLUEPRINT: 60,
}

PERSONAL_FIELDS = {"email", "full_name", "phone", "requester", "user", "custodian"}


def _redact(payload: dict) -> dict:
    """Data minimisation (FR-1.5): drop personal fields before anything leaves the server."""
    return {k: (_redact(v) if isinstance(v, dict) else v) for k, v in payload.items() if k not in PERSONAL_FIELDS}


def _input_ref(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:32]


class AIGateway:
    def __init__(self, provider=None):
        self._provider = provider  # tests inject a fake provider

    @property
    def provider(self):
        return self._provider or get_provider(settings.AI_PROVIDER)

    # --- public operations (class diagram) ---
    def classify(self, asset_text: dict, user=None) -> AIResult:
        return self._call(AICapability.CLASSIFY, "classify", asset_text, user)

    def recommend_action(self, asset_profile: dict, user=None) -> AIResult:
        return self._call(AICapability.RECOMMEND, "recommend_action", asset_profile, user)

    def chat(self, prompt: dict, user=None) -> AIResult:
        return self._call(AICapability.CHAT, "chat", prompt, user)

    def summarize(self, report_content: dict, user=None) -> AIResult:
        return self._call(AICapability.SUMMARIZE, "summarize", report_content, user)

    def draft_blueprint(self, description: dict, user=None) -> AIResult:
        return self._call(AICapability.BLUEPRINT, "draft_blueprint", description, user)

    # --- internals ---
    def _call(self, capability: str, method: str, payload: dict, user) -> AIResult:
        mv = ModelVersion.objects.filter(capability=capability, status=ModelStatus.ACTIVE).first()
        if mv is None:
            return self._log(None, capability, payload, user, AIResult(AIOutcome.UNAVAILABLE, explanation="No active model"), 0)

        clean = _redact(payload)
        started = time.monotonic()
        # Not a `with` block: leaving one waits for the thread, which would defeat the time limit.
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            fut = pool.submit(getattr(self.provider, method), clean, mv)
            raw: AIResult = fut.result(timeout=TIME_LIMITS.get(capability, 10))
        except concurrent.futures.TimeoutError:
            raw = AIResult(AIOutcome.TIMEOUT, explanation="AI service did not answer in time")
        except Exception as exc:  # provider bugs must never break the calling workflow (NFR-26)
            raw = AIResult(AIOutcome.ERROR, explanation=type(exc).__name__)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        latency = int((time.monotonic() - started) * 1000)

        if raw.status == AIOutcome.OK and mv.is_low_confidence(raw.confidence):
            raw.status = AIOutcome.LOW_CONFIDENCE
        raw.model_version_id = mv.pk
        return self._log(mv, capability, payload, user, raw, latency)

    def _log(self, mv, capability, payload, user, result: AIResult, latency: int) -> AIResult:
        rec = AIInferenceRecord.objects.create(
            model_version=mv, user=user if getattr(user, "pk", None) else None, capability=capability,
            input_ref=_input_ref(payload), output_summary=str(result.value)[:500] if result.value is not None else "",
            confidence=result.confidence, latency_ms=latency, outcome=result.status,
        )
        result.inference_id = rec.pk
        return result
