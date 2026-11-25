"""Deterministic provider for tests, demos without internet, and the 'AI is down' walk-through."""
from ..models import AIOutcome
from ..result import AIResult


class Provider:
    # concept (from the matching synonym table) -> category name in the demo data
    CONCEPT_CATEGORY = {"monitor": "Monitors", "projector": "Projectors", "dock": "Docking stations", "chair": "Chairs",
                        "shelf": "Shelving", "whiteboard": "Whiteboards", "oscilloscope": "Oscilloscopes",
                        "power": "Power supplies", "printer": "3D printers", "table": "Furniture", "computer": "IT Equipment"}

    def classify(self, payload, mv):
        """Offline stand-in for AI 1: reads the text with the bilingual synonym table; cannot see photos."""
        import re

        from apps.matching.embeddings import concepts_in  # local import: providers sit below business modules
        text = " ".join(str(payload.get(k, "")) for k in ("name", "description", "specifications"))
        cats = {c.split("/")[-1].strip().lower(): c for c in payload.get("categories", [])}
        found = [c for c in concepts_in(text) if self.CONCEPT_CATEGORY.get(c, "").lower() in cats]
        serial = re.search(r"\b(?:s/?n|serial(?: number)?)[\s:#-]*([A-Z0-9-]{5,})", text, re.I)
        sizes = re.findall(r"(\d{2})[\s-]*(?:inch|in\b|\")", text, re.I)
        if not found:
            return AIResult(AIOutcome.OK, value={"category": None, "tags": [], "missingFields": ["category"],
                                                 "serialNumber": serial.group(1) if serial else None}, confidence=0.30,
                            explanation="no known keywords")
        cat = self.CONCEPT_CATEGORY[sorted(found)[0]]
        tags = sorted(found) + [f"{s}-inch" for s in sizes[:1]]
        value = {"category": cats[cat.lower()], "subcategory": cat, "tags": tags,
                 "standardDescription": f"{cat[:-1] if cat.endswith('s') else cat}" + (f", {sizes[0]} inch" if sizes else "") + ".",
                 "serialNumber": serial.group(1) if serial else None, "conditionGuess": None,
                 "missingFields": []}
        return AIResult(AIOutcome.OK, value=value, confidence=0.82, explanation=f"text mentions {', '.join(sorted(found))}")

    def recommend_action(self, payload, mv):
        return AIResult(AIOutcome.UNAVAILABLE, explanation="fake provider has no advice")

    def chat(self, payload, mv):
        return AIResult(AIOutcome.NO_EVIDENCE, value={"text": "I don't know.", "citations": []})

    def summarize(self, payload, mv):
        """A plain paragraph made only from the totals, so demos without internet still show the review flow."""
        t = payload.get("totals", {})
        if "requests" in t:
            if not t["requests"]:
                return AIResult(AIOutcome.OK, value={"text": "No requests were sent in this period.", "claims": []})
            parts = [f"{t['requests']} request{'s' if t['requests'] != 1 else ''} asked for {t['units_requested']} "
                     f"unit{'s' if t['units_requested'] != 1 else ''} in this period."]
            if t.get("approval_rate_pct") is not None:
                parts.append(f"Of the decided requests, {t['approved']} approved and {t['rejected']} rejected: an approval rate of {t['approval_rate_pct']}%.")
            if t.get("transfers_completed"):
                parts.append(f"{t['transfers_completed']} transfers were completed, moving {t['units_moved']} units "
                             f"worth about AED {t['value_reused_aed']:,} that did not have to be bought new.")
            if t.get("top_categories"):
                parts.append(f"{t['top_categories'][0]['category']} was the most requested category.")
            parts.append("Values are estimates entered by custodians.")
            text = " ".join(parts)
        else:
            text = "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in t.items()) or "No data in this period."
        return AIResult(AIOutcome.OK, value={"text": text, "claims": []}, confidence=None)

    def draft_blueprint(self, payload, mv):
        """Offline stand-in: picks the closest template from keywords, so the review screen can be demonstrated."""
        from apps.blueprint.services import TEMPLATES  # local import: providers sit below the business modules
        text = str(payload.get("description", "")).lower()
        key = "hospital" if any(w in text for w in ("hospital", "clinic", "ward", "مستشفى")) else \
              "school" if any(w in text for w in ("school", "grade", "teacher", "مدرسة")) else "university"
        value = {k: v for k, v in TEMPLATES[key].items() if k != "label"}
        return AIResult(AIOutcome.OK, value=value, confidence=0.5, explanation=f"offline draft from the {key} template")
