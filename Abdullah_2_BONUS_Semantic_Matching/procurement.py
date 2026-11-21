"""Feature 3: check the catalogue before buying.

One more way into the existing matching flow (`services._run`): the same hard rules, embeddings, eight factors
and explanations as Find, with one difference: items with fewer free units than needed are kept and marked
partial. Money comes from the existing net-cost comparison (sustainability.services.net_cost_comparison), so a
saving here is worked out exactly as on "Reuse or buy new?".

Nothing here requests, reserves or approves anything: the page lists alternatives and links to the normal
request form. A MatchResultSet is saved, as for every Find search, so the suggestions can be explained later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.utils.translation import gettext as _

from apps.access.models import User
from apps.access.permissions import has_any
from apps.catalogue.models import Category
from apps.common.errors import Forbidden, ValidationFailed

from . import services
from .engine import Need

CAN_CHECK = ("request.submit", "request.approve")


def may_check(user: User) -> bool:
    return any(has_any(user, p) for p in CAN_CHECK)


@dataclass
class Plan:
    """What the need is: written by the person on the form."""

    description: str
    quantity: int = 1
    category: Category | None = None
    specifications: str = ""
    condition: str = "ANY"
    campus: str = ""
    needed_by: date | None = None
    unit_price: Decimal | None = None   # their estimated purchase price per unit; None = use each item's value


@dataclass
class Alternative:
    rec: object                  # MatchRecommendation (or an Asset when ranking was unavailable)
    asset: object
    take: int                    # units this item could cover (never more than free or than needed)
    partial: list[str]           # why it only meets part of the need
    buy_new: Decimal | None      # price of `take` new units
    reuse_cost: Decimal          # transfer + repair (+ storage 0) for `take` units
    avoided: Decimal | None      # buy_new - reuse_cost
    price_source: str
    cost_lines: list[tuple[str, str]]
    feasible: str
    reasons: list[str]

    @property
    def weak(self) -> bool:
        return hasattr(self.rec, "is_weak") and self.rec.is_weak()


@dataclass
class Result:
    plan: Plan
    ranked: bool
    alternatives: list[Alternative] = field(default_factory=list)
    covered: int = 0                       # units a combination of the best items could cover, each counted once
    combined_avoided: Decimal | None = None
    combined_from: list[str] = field(default_factory=list)
    still_to_buy: int = 0
    considered: int = 0


def _partial_reasons(plan: Plan, rec, asset, free: int) -> list[str]:
    out = []
    if free < plan.quantity:
        out.append(_("Only %(n)s of the %(q)s units you need are free.") % {"n": free, "q": plan.quantity})
    if hasattr(rec, "factor_scores"):
        f2 = (rec.factor_scores.get("factors") or {}).get("f2")
        if plan.specifications.strip():
            if f2 is not None and f2 < 1:
                out.append(_("Only some of your specifications appear in the listing; check with the custodian."))
            else:
                out.append(_("Your specifications appear in the listing, but nobody has checked them on the item."))
    else:
        out.append(_("Not ranked: keyword match only, so check that it fits."))
    return out


def check(user: User, plan: Plan) -> Result:
    """Run the check. Raises Forbidden / ValidationFailed for the form; never touches assets or requests."""
    if not may_check(user):
        raise Forbidden("Not permitted: procurement check")
    plan.description = (plan.description or "").strip()
    if len(plan.description) < 2:
        raise ValidationFailed("Describe what you need in a few words")
    if not 1 <= plan.quantity <= 999:
        raise ValidationFailed("Quantity must be between 1 and 999")
    if plan.unit_price is not None and plan.unit_price < 0:
        raise ValidationFailed("Price cannot be negative")

    d = user.department
    need = Need(text=plan.description, specs=plan.specifications, quantity=plan.quantity, preferred_condition=plan.condition or "ANY",
                campus=plan.campus or ((d.campus if d else "") or ""), building="" if plan.campus else ((d.building if d else "") or ""),
                required_date=plan.needed_by)
    outcome = services._run(need, category=plan.category, exclude_unit_id=user.department_id, user=user, request=None,
                            query_text=plan.description, allow_partial=True)

    from apps.sustainability.services import net_cost_comparison  # one formula for every saving shown

    def alt(rec, asset) -> Alternative:
        free = asset.unreserved_quantity
        take = max(1, min(free, plan.quantity))
        nc = net_cost_comparison(asset, take, plan.unit_price, destination_campus=need.campus, required_date=plan.needed_by)
        source = _("your estimated price") if plan.unit_price is not None else _("the item's estimated value")
        return Alternative(rec, asset, take, _partial_reasons(plan, rec, asset, free), nc.buy_new, nc.reuse_total, nc.avoided,
                           source, nc.inputs, nc.feasible, [str(r) for r in nc.reasons])

    if outcome.ranked:
        alts = [alt(r, r.asset) for r in outcome.suitable + outcome.weak]
    else:
        alts = [alt(a, a) for a in outcome.fallback]
    res = Result(plan, outcome.ranked, alts, considered=outcome.considered)

    # Combination: best suitable items first until the quantity is covered. Each unit is counted once, so the
    # total is not the sum of every card (the cards are alternatives to each other).
    left, total, used = plan.quantity, Decimal(0), []
    known = True
    for a in alts:
        if left <= 0:
            break
        if a.weak or a.feasible == "no" or not outcome.ranked or (a.avoided is not None and a.avoided <= 0):
            continue  # weak, not possible, unranked, or dearer than buying new: not part of the suggestion
        n = min(a.take, left)
        if n <= 0:
            continue
        nc = net_cost_comparison(a.asset, n, plan.unit_price, destination_campus=need.campus, required_date=plan.needed_by)
        if nc.avoided is None:
            known = False
        else:
            total += nc.avoided
        used.append(f"{n} × {a.asset.name}")
        left -= n
    res.covered = plan.quantity - left
    res.still_to_buy = max(0, left)
    res.combined_from = used
    res.combined_avoided = total if (used and known) else None
    return res
