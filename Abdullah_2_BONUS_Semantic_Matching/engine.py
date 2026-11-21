"""MatchingEngine and ExplanationBuilder (Section 9.2-9.3). OWNER: matching module.

Order of work: hard rules (services.py, in SQL) -> similarity -> eight factors -> score -> explanation.
Everything here is plain arithmetic on numbers we can show to the user. No LLM writes a score or a reason.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.common.enums import Condition, PreferredCondition, Urgency
from apps.sustainability.calculator import (LEAD_DAYS_OTHER_CAMPUS, LEAD_DAYS_SAME_CAMPUS, REPAIR_DAYS, REPAIR_SHARE_POOR,
                                            TRANSFER_COST_OTHER_CAMPUS, TRANSFER_COST_SAME_CAMPUS)

from .embeddings import concepts_in, cosine, normalise, tokens

# Table 9.2. Stored with the RANK ModelVersion.config in production; these are the defaults.
DEFAULT_WEIGHTS = {"f1": 0.30, "f2": 0.20, "f3": 0.10, "f4": 0.10, "f5": 0.10, "f6": 0.10, "f7": 0.05, "f8": 0.05}
HIGH_URGENCY_WEIGHTS = {**DEFAULT_WEIGHTS, "f5": 0.15, "f7": 0.00}

FACTOR_LABELS = {
    "f1": gettext_lazy("similar purpose"), "f2": gettext_lazy("specifications met"), "f3": gettext_lazy("condition fit"),
    "f4": gettext_lazy("close by"), "f5": gettext_lazy("ready by the required date"),
    "f6": gettext_lazy("low repair + transfer cost"), "f7": gettext_lazy("sustainability benefit"),
    "f8": gettext_lazy("enough units"),
}

# Cosine similarity is rescaled to 0-1 between "unrelated" and "same thing" for each embedder, because the two
# embedders spread their scores differently. Below MIN_RELEVANCE an item is not a candidate at all.
SIMILARITY_BOUNDS = {"lexical": (0.06, 0.50), "sentence-transformers": (0.20, 0.75)}
MIN_RELEVANCE = 0.35

# Transfer and repair cost assumptions (TRANSFER_COST_*, REPAIR_*, LEAD_DAYS_*) live in
# sustainability/calculator.py, shared with the net-cost comparison so the two never disagree.
CARBON_FULL_MARKS_KG = Decimal("100")  # f7 reaches 1 when the transfer avoids 100 kg CO2e or more

STOPWORDS = set("a an the and or for of to in on at with by from is are be it this that we our need needs needed "
                "want some any one two three per new used good fair poor please".split())
SIZE = re.compile(r"(\d+(?:\.\d+)?)[\s-]*(inch|in|\"|cm|mm|m|l|kg|w|seat|seats|tb|gb|بوصه|انش|سم)(?=\W|$)", re.I)


@dataclass
class Need:
    """What is being looked for. Built from a saved ResourceRequest or from the Find box."""

    text: str
    specs: str = ""
    quantity: int = 1
    preferred_condition: str = PreferredCondition.ANY
    urgency: str = Urgency.MEDIUM
    campus: str = ""
    building: str = ""
    required_date: date | None = None


@dataclass
class Candidate:
    asset: object
    factors: dict[str, float]  # f1..f8 in 0-1
    notes: list[str] = field(default_factory=list)  # penalties, e.g. "other campus"
    known: int = 0  # how many optional inputs were known (for confidence)
    of: int = 0
    cost: Decimal | None = None
    explain_cost: str = ""
    neutral: set = field(default_factory=set)  # factors set to a middle value because the input was missing


@dataclass
class Ranked:
    asset: object
    score: float  # 0-100
    factors: dict[str, float]
    contributions: dict[str, float]
    confidence: float | None
    explanation: str
    notes: list[str]
    estimate_notes: str


def weights_for(urgency: str) -> dict[str, float]:
    return HIGH_URGENCY_WEIGHTS if urgency == Urgency.HIGH else DEFAULT_WEIGHTS


def score(factors: dict[str, float], weights: dict[str, float]) -> tuple[float, dict[str, float]]:
    """score = round(100 x sum(w_i * f_i)). Returns (score, contributions in points)."""
    contributions = {k: round(100 * weights[k] * factors.get(k, 0.0), 2) for k in weights}
    return round(sum(contributions.values()), 2), contributions


def rescale(cos: float, embedder: str) -> float:
    lo, hi = SIMILARITY_BOUNDS.get(embedder, SIMILARITY_BOUNDS["lexical"])
    return max(0.0, min(1.0, (cos - lo) / (hi - lo)))


def _clamp(x) -> float:
    return float(max(0, min(1, x)))


NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
                "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
                "a pair of": 2, "couple of": 2, "واحد": 1, "اثنان": 2, "اثنين": 2, "ثلاثه": 3, "اربعه": 4, "خمسه": 5,
                "سته": 6, "سبعه": 7, "ثمانيه": 8, "تسعه": 9, "عشره": 10, "عشرين": 20}


def guess_quantity(text: str) -> int | None:
    """'Two 24-inch monitors' -> 2. A number followed by a size unit ('24-inch') is a size, not a quantity."""
    t = normalise(text)
    sizes = {m.start(1) for m in SIZE.finditer(t)}
    for m in re.finditer(r"\b(\d{1,3})\b", t):
        if m.start(1) not in sizes:
            return int(m.group(1)) or None
    for word, n in sorted(NUMBER_WORDS.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", t):
            return n
    if any(len(w) > 4 and (w.endswith("تان") or w.endswith("تين")) for w in t.split()):
        return 2  # Arabic dual: شاشتان = two screens
    return None


def _spec_terms(text: str) -> set[str]:
    return {t for t in tokens(text) if t not in STOPWORDS and len(t) > 1}


def _sizes(text: str) -> dict[str, float]:
    unit = {"in": "inch", '"': "inch", "بوصه": "inch", "انش": "inch", "سم": "cm"}
    return {unit.get(u.lower(), u.lower()): float(n) for n, u in SIZE.findall(normalise(text or ""))}


class MatchingEngine:
    def __init__(self, embedder_name: str = "lexical"):
        self.embedder_name = embedder_name

    # ------------------------------------------------------------------ factors
    def factors(self, need: Need, asset, cos: float, emission_kg: Decimal | None, today: date | None = None) -> Candidate | None:
        """f1..f8 for one asset that already passed the hard rules. None if it is not relevant enough."""
        today = today or date.today()
        notes: list[str] = []
        known, of = 0, 0
        neutral: set[str] = set()
        asset_text = " ".join([asset.name, asset.category.name, asset.category.name_ar, asset.description, asset.specifications])

        # f1 similar purpose (semantic similarity, rescaled)
        f1 = rescale(cos, self.embedder_name)
        if f1 < MIN_RELEVANCE:
            return None

        # f2 specifications met: share of the must-have terms found in the item; a different size halves it.
        wanted = _spec_terms(need.specs) if need.specs.strip() else {t for t in _spec_terms(need.text) if any(c.isdigit() for c in t)}
        of += 1
        if wanted:
            known += 1
            have = _spec_terms(asset_text) | concepts_in(asset_text)
            wanted_concepts = {t: (concepts_in(t) or {t}) for t in wanted}
            met = sum(1 for t, cs in wanted_concepts.items() if t in have or cs & have)
            f2 = met / len(wanted)
            want_size, have_size = _sizes(need.specs or need.text), _sizes(asset_text)
            if any(u in have_size and abs(have_size[u] - v) > 0.01 for u, v in want_size.items()):
                f2 *= 0.5
                notes.append(_("different size"))
            elif want_size and not any(u in have_size for u in want_size):
                notes.append(_("size not listed"))
        else:
            f2 = 0.7  # nothing specific was asked for: neither a match nor a miss
            neutral.add("f2")

        # f3 condition fit
        if need.preferred_condition in ("", PreferredCondition.ANY):
            f3 = 1.0
        else:
            gap = Condition.rank(asset.condition) - Condition.rank(need.preferred_condition)
            f3 = 1.0 if gap >= 0 else (0.5 if gap == -1 else 0.0)
            if gap < 0:
                notes.append(_("below the condition you asked for"))

        # f4 location
        same_campus = bool(need.campus) and asset.location_campus.strip().lower() == need.campus.strip().lower()
        of += 1
        if need.campus:
            known += 1
        if same_campus and need.building and asset.location_building.strip().lower() == need.building.strip().lower():
            f4 = 1.0
        elif same_campus:
            f4 = 0.8
        else:
            f4 = 0.4
            notes.append(_("other campus (%(c)s)") % {"c": asset.location_campus})

        # f5 ready by the required date: lead time for the move, plus repairs for a Poor item
        lead = LEAD_DAYS_SAME_CAMPUS if same_campus else LEAD_DAYS_OTHER_CAMPUS
        f5 = 1.0
        if asset.condition == Condition.POOR:
            f5 = 0.5
            lead += REPAIR_DAYS
            notes.append(_("may need repair first"))
        if need.required_date:
            days = (need.required_date - today).days
            if days < lead:
                f5 *= 0.4
                notes.append(_("tight for the date you need it"))

        # f6 cost of reuse compared with buying new (repair + transfer) / (value x qty)
        move_cost = TRANSFER_COST_SAME_CAMPUS if same_campus else TRANSFER_COST_OTHER_CAMPUS
        of += 1
        cost = None
        explain_cost = ""
        if asset.estimated_value:
            known += 1
            new_value = asset.estimated_value * need.quantity
            repair = asset.estimated_value * need.quantity * REPAIR_SHARE_POOR if asset.condition == Condition.POOR else Decimal(0)
            cost = move_cost + repair
            f6 = _clamp(1 - cost / new_value) if new_value else 0.5
            explain_cost = _("Reuse costs about AED %(c)s (move %(m)s + repair %(r)s) against AED %(n)s to buy new.") % {
                "c": f"{cost:,.0f}", "m": f"{move_cost:,.0f}", "r": f"{repair:,.0f}", "n": f"{new_value:,.0f}"}
        else:
            f6 = 0.5
            neutral.add("f6")
            notes.append(_("value unknown"))

        # f7 sustainability benefit: carbon of a new purchase that reuse avoids (locally selected factor)
        of += 1
        if emission_kg is not None:
            known += 1
            f7 = _clamp(emission_kg * need.quantity / CARBON_FULL_MARKS_KG)
        else:
            f7 = 0.5
            neutral.add("f7")

        # f8 enough units: all units from one item is best; a big surplus is used better by a big request
        free = asset.unreserved_quantity
        if free < need.quantity:  # only reachable from the procurement check, which allows partial matches
            f8 = _clamp(free / need.quantity)
            notes.append(_("only %(n)s of %(q)s free") % {"n": free, "q": need.quantity})
        else:
            f8 = 1.0 if free == need.quantity else _clamp(0.8 + 0.2 * need.quantity / max(free, 1))

        of += 1
        if asset.purchase_date:
            known += 1

        return Candidate(asset, {"f1": round(f1, 3), "f2": round(f2, 3), "f3": f3, "f4": f4, "f5": round(f5, 3),
                                 "f6": round(f6, 3), "f7": round(f7, 3), "f8": round(f8, 3)},
                         notes, known, of, cost, explain_cost, neutral)

    # ------------------------------------------------------------------ ranking
    def rank(self, candidates: list[Candidate], urgency: str, keep_below: float = 55) -> list[Ranked]:
        """Score, sort (ties: readiness, then lower cost), drop < keep_below, explain."""
        w = weights_for(urgency)
        out = []
        for c in candidates:
            s, contrib = score(c.factors, w)
            if s < keep_below:
                continue
            confidence = round(0.5 + 0.5 * (c.known / c.of), 3) if c.of else None
            out.append(Ranked(c.asset, s, c.factors, contrib, confidence, self.explain(c, contrib), c.notes, c.explain_cost))
        out.sort(key=lambda r: (-r.score, -r.factors["f5"], float(r.asset.estimated_value or 0)))
        return out

    def explain(self, c: Candidate, contributions: dict[str, float]) -> str:
        """Built from the contributions, never by an LLM (Section 9.3). First line is the one-line reason."""
        strong = [k for k, v in sorted(contributions.items(), key=lambda kv: -kv[1])
                  if c.factors[k] >= 0.7 and k not in c.neutral][:3]
        sep = "، " if (get_language() or "").startswith("ar") else ", "
        if strong:
            line = _("Good fit: %(why)s.") % {"why": sep.join(str(FACTOR_LABELS[k]) for k in strong)}
        else:
            line = _("Partly fits what you described.")
        if c.notes:
            line += " " + _("Watch: %(n)s.") % {"n": sep.join(c.notes[:3])}
        return line

    # ------------------------------------------------------------------ similarity helper for tests
    @staticmethod
    def similarity(query_vec, asset_vec) -> float:
        return cosine(query_vec, asset_vec)
