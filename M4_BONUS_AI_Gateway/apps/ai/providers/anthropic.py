"""Adapter for Anthropic's API (ADR-3). Only the AI Gateway calls this.

Each method asks the model for JSON that matches the contract in Table 9.1 and parses it defensively:
anything that is not the expected JSON becomes AIOutcome.ERROR, never an exception in the caller.
Set AI_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env; ANTHROPIC_MODEL picks the model.
"""
from __future__ import annotations

import json
import re

from django.conf import settings

from ..models import AIOutcome
from ..result import AIResult

ADVICE_SYSTEM = """You explain a sustainable-action recommendation for one university asset to the staff member who \
looks after it. The action was already chosen by fixed rules; you only explain it in plain words.

Rules:
- Explain the action in "rule_result" and why, using only the facts, estimates and reasons given. Never choose a \
different action and never add, calculate or round numbers; if you mention a figure, copy it exactly as written.
- Mention one alternative from "rule_result.alternatives" and its trade-off if useful, and anything listed in "missing".
- Say that nothing changes until a person starts the step and, for end-of-life steps, a reviewer approves it.
- 50 to 110 words, plain prose, no headings, no lists, no markdown, no names of people.
- Write in the language given in "language" ("ar" = Modern Standard Arabic, otherwise English).

Reply with JSON only: {"text": "<the explanation>"}"""

SUMMARY_SYSTEM = """You write the short summary at the top of a university report about reusing surplus assets \
(furniture, IT and lab equipment moved between departments instead of buying new).

Rules:
- Use only numbers that appear in "totals" (or the period dates). Never calculate, estimate or round new numbers.
- If a total is null, say it is not available; do not guess it.
- 80 to 140 words, plain prose, no headings, no bullet points, no markdown.
- Start with the most important result, then one or two patterns (top categories, approvals, transfers), \
then one sentence on a limitation from "limitations".
- Write in the language given in "language" ("ar" = Modern Standard Arabic, otherwise English).
- Neutral, factual tone. No advice, no praise, no names of people.

Reply with JSON only: {"text": "<the summary>", "claims": [{"value": "<number as written>", "source": "<totals key>"}]}"""


def _json(text: str) -> dict:
    """First JSON object in the reply (models sometimes wrap JSON in prose or code fences)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    return json.loads(m.group(0))


BLUEPRINT_SYSTEM = """You help an administrator set up an asset-reuse platform for their institution. From their \
description, draft the institution's units, member types and approval routes.

Return JSON only, with exactly this shape:
{"units": [{"name": str, "unit_type": str, "parent": str|null}],
 "roles": [{"name": str, "permissions": [codes], "approval_limit": number|null}],
 "rules": [{"name": str, "priority": int, "category": null, "min_value": number|null, "max_value": number|null,
            "approver_role": str, "approver_scope": "OWNING_UNIT"|"PARENT_UNIT"|"INSTITUTION"}]}

Rules:
- Use only permission codes from "permissions" in the input. approval_limit is in AED; null means no limit.
- Every rule's approver_role must be one of your roles and that role must have "request.approve".
- A unit's parent must be another unit in your list (or null for the top unit). Use the institution's own words.
- Lower priority numbers are checked first; end with a catch-all rule (no min/max).
- Keep it small: at most 12 units, 7 roles and 5 rules. Do not invent people or names of real persons.
- If the description is in Arabic, write names in Arabic."""


CLASSIFY_SYSTEM = """You help a university register surplus equipment for reuse. From the item's text and, if \
present, its photo, suggest how to file it.

Return JSON only:
{"category": str|null, "subcategory": str|null, "tags": [str], "standardDescription": str,
 "materialType": str|null, "serialNumber": str|null, "conditionGuess": "NEW"|"GOOD"|"FAIR"|"POOR"|null,
 "missingFields": [str], "confidence": number}

Rules:
- category/subcategory must be copied exactly from "categories" in the input (the path text); null if none fits.
- serialNumber only if you can read it on a label in the photo or it is in the text; never guess one.
- conditionGuess only from visible evidence in the photo; otherwise null.
- tags: 2 to 6 short lowercase search words; standardDescription: one plain sentence, no marketing words.
- confidence: 0 to 1, how sure you are about the category."""


class Provider:
    def __init__(self):
        import anthropic  # optional dependency, see requirements-ai.txt

        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY or None, max_retries=1)

    @staticmethod
    def _model(mv) -> str:
        return mv.model_name if mv is not None and mv.provider == "anthropic" else settings.ANTHROPIC_MODEL

    def _not_yet(self):
        return AIResult(AIOutcome.UNAVAILABLE, explanation="Not implemented yet")

    def _ask(self, mv, system: str, payload: dict, max_tokens: int = 800) -> str:
        msg = self.client.messages.create(
            model=self._model(mv), max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content)

    def summarize(self, payload, mv):
        """AI feature 5: totals in, one paragraph out. The caller checks every number in the text."""
        try:
            data = _json(self._ask(mv, SUMMARY_SYSTEM, payload))
        except (ValueError, json.JSONDecodeError) as exc:
            return AIResult(AIOutcome.ERROR, explanation=f"unreadable reply: {exc}")
        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            return AIResult(AIOutcome.ERROR, explanation="reply had no text")
        claims = data.get("claims") if isinstance(data.get("claims"), list) else []
        return AIResult(AIOutcome.OK, value={"text": text.strip(), "claims": claims}, confidence=None)

    def classify(self, payload, mv):
        """AI feature 1 (optional): text + optional photo -> category, tags, description, serial number."""
        payload = dict(payload)
        image = payload.pop("image", None)
        content = []
        if image:
            content.append({"type": "image", "source": {"type": "base64", "media_type": image["media_type"], "data": image["data"]}})
        content.append({"type": "text", "text": json.dumps(payload, ensure_ascii=False, default=str)})
        try:
            msg = self.client.messages.create(model=self._model(mv), max_tokens=600, system=CLASSIFY_SYSTEM,
                                              messages=[{"role": "user", "content": content}])
            data = _json("".join(getattr(b, "text", "") for b in msg.content))
        except (ValueError, json.JSONDecodeError) as exc:
            return AIResult(AIOutcome.ERROR, explanation=f"unreadable reply: {exc}")
        try:
            conf = max(0.0, min(1.0, float(data.pop("confidence", 0))))
        except (TypeError, ValueError):
            conf = None
        return AIResult(AIOutcome.OK, value=data, confidence=conf)

    def recommend_action(self, payload, mv):
        """Feature 2 (optional): re-word the rule-based advice. The caller shows it labelled as AI-written."""
        try:
            data = _json(self._ask(mv, ADVICE_SYSTEM, payload, max_tokens=500))
        except (ValueError, json.JSONDecodeError) as exc:
            return AIResult(AIOutcome.ERROR, explanation=f"unreadable reply: {exc}")
        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            return AIResult(AIOutcome.ERROR, explanation="reply had no text")
        return AIResult(AIOutcome.OK, value={"text": text.strip()}, confidence=None)

    def chat(self, payload, mv):
        return self._not_yet()  # AI feature 4 (optional, not planned)

    def draft_blueprint(self, payload, mv):
        """Bonus: plain words in, a structured draft out. The admin reviews and publishes; nothing is written here."""
        try:
            data = _json(self._ask(mv, BLUEPRINT_SYSTEM, payload, max_tokens=2000))
        except (ValueError, json.JSONDecodeError) as exc:
            return AIResult(AIOutcome.ERROR, explanation=f"unreadable reply: {exc}")
        if not isinstance(data.get("units"), list) or not isinstance(data.get("roles"), list):
            return AIResult(AIOutcome.ERROR, explanation="reply missing units or roles")
        return AIResult(AIOutcome.OK, value=data, confidence=None)
