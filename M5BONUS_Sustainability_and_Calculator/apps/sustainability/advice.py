"""Feature 2: sustainable-action recommendations (feature 4.11, offline rule version).

Plain, deterministic rules over what the system already knows about one asset. Nothing here writes anything:
the result is worked out each time it is shown, and every action links to the existing workflow (publish,
report a problem, propose end of life), where the normal permission checks and state machines apply. The AI
gateway may later re-word the explanation; it never chooses the action or produces a number (rules 9 and 10).

Rule constants are starting assumptions for the prototype, listed on screen next to the result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from apps.access.permissions import can
from apps.catalogue.models import Asset, AssetState
from apps.common.enums import Condition, EndOfLifeAction
from apps.resource_requests.models import RequestStatus, ResourceRequest

from .calculator import REPAIR_SHARE_POOR, TRANSFER_COST_OTHER_CAMPUS, TRANSFER_COST_SAME_CAMPUS

# --- rule constants (prototype assumptions, shown on screen) ---
REPAIR_LIMIT_SHARE = Decimal("0.5")   # repairs (spent + next) above half the item's value: repairing is not worth it
FAILED_REPAIRS_LIMIT = 2              # two unsuccessful repairs: stop repairing
OLD_AGE_MONTHS = 84                   # 7 years: "older item" for these rules (a rule of thumb, not a manufacturer figure)

ADVISORS = ("asset.register", "asset.custody", "maintenance.record", "eol.propose", "eol.approve", "sustainability.review")
GONE = (AssetState.DONATED, AssetState.RECYCLED, AssetState.DISPOSED)
EOL_FROM = (AssetState.AVAILABLE, AssetState.UNDER_MAINTENANCE, AssetState.RETIRED, AssetState.REGISTERED)

ICON = {EndOfLifeAction.RETAIN: "check", EndOfLifeAction.TRANSFER: "truck", EndOfLifeAction.REPAIR: "wrench",
        EndOfLifeAction.REFURBISH: "wrench", EndOfLifeAction.DONATE: "leaf", EndOfLifeAction.DISASSEMBLE: "box",
        EndOfLifeAction.RECYCLE: "leaf", EndOfLifeAction.DISPOSE: "alert", EndOfLifeAction.RETIRE: "alert"}

TITLE = {
    EndOfLifeAction.RETAIN: _l("Keep using or reuse it"),
    EndOfLifeAction.TRANSFER: _l("Transfer it to another unit"),
    EndOfLifeAction.REPAIR: _l("Repair or refurbish it"),
    EndOfLifeAction.REFURBISH: _l("Repair or refurbish it"),
    EndOfLifeAction.DONATE: _l("Donate it"),
    EndOfLifeAction.DISASSEMBLE: _l("Take it apart for usable parts"),
    EndOfLifeAction.RECYCLE: _l("Recycle it"),
    EndOfLifeAction.DISPOSE: _l("Dispose of it (last option)"),
    EndOfLifeAction.RETIRE: _l("Retire it"),
}


def can_advise(user, asset: Asset) -> bool:
    """Who sees the advice: the custodian and people who look after, decide on or review this unit's items."""
    if not getattr(user, "is_authenticated", False):
        return False
    return asset.custodian_id == user.pk or any(can(user, a, asset.owner_department) for a in ADVISORS)


# ----------------------------------------------------------------------------- what we know

@dataclass
class Facts:
    asset: Asset
    state: str
    condition: str
    published: bool
    free: int
    reserved: int
    age_months: int | None
    value: Decimal | None
    repairs: int
    failed_repairs: int
    repair_spent: Decimal
    open_maintenance: object | None
    open_proposal: object | None
    demand_requests: int
    demand_units: int
    missing: list[str] = field(default_factory=list)


def facts_for(asset: Asset) -> Facts:
    """Read-only snapshot of the inputs the rules use. Sustainability sits above Life Cycle and Requests in the
    import order, so reading their tables here is allowed (CLAUDE.md rule 2)."""
    from apps.lifecycle.models import EndOfLifeProposal, EolStatus, MaintenanceRecord, RepairAction, RepairOutcome
    from apps.lifecycle.services import OPEN_MAINTENANCE

    repairs = list(RepairAction.objects.filter(maintenance__asset=asset).values_list("outcome", "cost"))
    cats = asset.category.descendant_ids() | ({asset.category.parent_id} if asset.category.parent_id else set())
    waiting = (ResourceRequest.objects.filter(status=RequestStatus.PENDING_APPROVAL, category_id__in=cats)
               .exclude(department_id=asset.owner_department_id).exclude(selected_asset__isnull=False))
    missing = []
    if asset.estimated_value is None:
        missing.append(_("Estimated value: without it, repair and reuse can't be compared in money."))
    if asset.purchase_date is None:
        missing.append(_("Purchase date: the item's age is unknown, so age is not used."))
    return Facts(
        asset=asset, state=asset.lifecycle_state, condition=asset.condition,
        published=asset.publication_status == "PUBLISHED", free=asset.unreserved_quantity, reserved=asset.reserved_quantity,
        age_months=asset.age(), value=asset.estimated_value,
        repairs=len(repairs), failed_repairs=sum(1 for o, _c in repairs if o == RepairOutcome.UNSUCCESSFUL),
        repair_spent=sum((c or Decimal(0) for _o, c in repairs), Decimal(0)),
        open_maintenance=MaintenanceRecord.objects.filter(asset=asset, status__in=OPEN_MAINTENANCE).order_by("-opened_at").first(),
        open_proposal=EndOfLifeProposal.objects.filter(asset=asset, status__in=[EolStatus.PENDING_REVIEW, EolStatus.APPROVED]).first(),
        demand_requests=waiting.count(), demand_units=sum(waiting.values_list("quantity", flat=True)),
        missing=missing,
    )


# ----------------------------------------------------------------------------- result

@dataclass
class Link:
    url: str
    label: str
    drawer: bool = False   # open in the side panel (hx-get) rather than as a page


@dataclass
class Option:
    action: str
    title: str
    why: list[str]
    tradeoff: str = ""
    link: Link | None = None
    advice_only: str = ""     # why there is no button (no workflow, no permission, or the state forbids it)

    @property
    def icon(self) -> str:
        return ICON.get(self.action, "leaf")


@dataclass
class Estimate:
    label: str
    value: str
    how: str


@dataclass
class Advice:
    asset: Asset
    facts: Facts
    recommended: Option | None
    alternatives: list[Option]
    estimates: list[Estimate]
    rules: list[str]
    ended: bool = False


def _url(name, *args, query="") -> str | None:
    try:
        return reverse(name, args=args) + (f"?{query}" if query else "")
    except NoReverseMatch:
        return None


def _money(x: Decimal) -> str:
    return f"AED {x.quantize(Decimal('1'), ROUND_HALF_UP):,}"


class _Links:
    """Workflow buttons for this person, only where the existing workflow would accept the step."""

    def __init__(self, user, f: Facts):
        self.user, self.f, self.a = user, f, f.asset
        self.dept = f.asset.owner_department

    def _no_permission(self) -> str:
        return _("Your role can't start this. Ask the unit's custodian.")

    def eol(self, action: str) -> tuple[Link | None, str]:
        f = self.f
        if f.open_proposal is not None:
            return None, _("An end-of-life proposal is already open for this item.")
        if f.reserved > 0:
            return None, _("Units are reserved for a transfer; end-of-life steps wait until it finishes.")
        if f.state not in EOL_FROM:
            return None, _("Not possible from the item's current state.")
        if not can(self.user, "eol.propose", self.dept):
            return None, self._no_permission()
        url = _url("lifecycle:propose", self.a.pk, query=f"action={action}")
        return (Link(url, _("Propose this (goes to review)"), drawer=True), "") if url else (None, "")

    def report(self) -> tuple[Link | None, str]:
        if self.f.open_maintenance is not None:
            if can(self.user, "maintenance.record", self.dept):
                url = _url("lifecycle:maintenance")
                return (Link(url, _("Open the maintenance board")), "") if url else (None, "")
            return None, _("A maintenance record is already open.")
        if self.f.state not in (AssetState.AVAILABLE, AssetState.REGISTERED, AssetState.TRANSFERRED):
            return None, _("Not possible from the item's current state.")
        if not can(self.user, "maintenance.record", self.dept):
            return None, self._no_permission()
        url = _url("lifecycle:report", self.a.pk)
        return (Link(url, _("Report a problem"), drawer=True), "") if url else (None, "")

    def our_assets(self, label, permission) -> tuple[Link | None, str]:
        if not can(self.user, permission, self.dept):
            return None, self._no_permission()
        url = _url("catalogue:mine")
        return (Link(url + f"?q={self.a.name[:40]}", label), "") if url else (None, "")


def _repair_not_worth_it(f: Facts) -> tuple[bool, list[str]]:
    why = []
    if f.failed_repairs >= FAILED_REPAIRS_LIMIT:
        why.append(_("%(n)s repairs have already failed.") % {"n": f.failed_repairs})
        return True, why
    if f.value:
        next_repair = f.value * REPAIR_SHARE_POOR if f.condition == Condition.POOR else Decimal(0)
        if f.repair_spent + next_repair > f.value * REPAIR_LIMIT_SHARE:
            why.append(_("Repairs spent so far (%(spent)s) plus the next estimated repair (%(next)s) are more than half the item's value (%(v)s).")
                       % {"spent": _money(f.repair_spent), "next": _money(next_repair), "v": _money(f.value)})
            return True, why
    return False, why


def recommend(user, asset: Asset) -> Advice:
    """Work out the recommended next step and its alternatives. Read-only."""
    f = facts_for(asset)
    L = _Links(user, f)
    rules = [
        _("Repair stops being worth it when repairs spent plus the next estimated repair exceed %(p)s%% of the item's value, or after %(n)s failed repairs.")
        % {"p": int(REPAIR_LIMIT_SHARE * 100), "n": FAILED_REPAIRS_LIMIT},
        _("Next repair of a Poor item is estimated at %(p)s%% of its value (the same assumption as \"Reuse or buy new?\").") % {"p": int(REPAIR_SHARE_POOR * 100)},
        _("An item counts as older after %(y)s years. This is a starting assumption, not a manufacturer's figure.") % {"y": OLD_AGE_MONTHS // 12},
        _("Demand means requests from other units, waiting for approval, in this category with no item chosen yet."),
    ]
    estimates = _estimates(f)

    if f.state in GONE:
        return Advice(asset, f, None, [], [], rules, ended=True)

    def opt(action, why, tradeoff="", link_info=(None, "")):
        link, reason = link_info
        return Option(action, str(TITLE[action]), why, tradeoff, link, reason if link is None else "")

    def no_workflow():
        return None, _("Advice only: the system has no disassembly workflow yet. If you go ahead, propose Recycle and list the parts you kept in the reason.")

    alts: list[Option] = []
    old = f.age_months is not None and f.age_months >= OLD_AGE_MONTHS
    good_enough = f.condition in (Condition.NEW, Condition.GOOD, Condition.FAIR)
    dispose = opt(EndOfLifeAction.DISPOSE, [], _("Last option: nothing is reused and nothing is recovered."), L.eol(EndOfLifeAction.DISPOSE))

    # 1. something is already in progress: respect it
    if f.open_proposal is not None:
        p = f.open_proposal
        rec = opt(p.action_type if p.action_type in TITLE else EndOfLifeAction.RETIRE,
                  [_("A proposal to %(a)s this item is already %(s)s. Let the review finish before starting anything else.")
                   % {"a": p.get_action_type_display().lower(), "s": p.get_status_display().lower()}],
                  link_info=(Link(_url("lifecycle:maintenance") + "?tab=eol", _("See the proposal")), "")
                  if can(user, "eol.propose", asset.owner_department) or can(user, "eol.approve", asset.owner_department) else (None, ""))
        return Advice(asset, f, rec, [], estimates, rules)

    if f.reserved > 0:
        rec = opt(EndOfLifeAction.RETAIN, [_("%(n)s unit(s) are reserved for an approved transfer. Let it finish: that is reuse already happening.") % {"n": f.reserved}],
                  _("Other steps wait until the transfer is received or cancelled."))
        return Advice(asset, f, rec, [], estimates, rules)

    # 2. retired: choose the final route, best first
    if f.state == AssetState.RETIRED:
        if good_enough:
            rec = opt(EndOfLifeAction.DONATE, [_("It is retired but still in %(c)s condition, so someone else can use it.") % {"c": asset.get_condition_display().lower()}],
                      _("It leaves the university's register; no internal unit can reuse it after that."), L.eol(EndOfLifeAction.DONATE))
            alts = [opt(EndOfLifeAction.RECYCLE, [], _("Recovers materials, but the working item is lost."), L.eol(EndOfLifeAction.RECYCLE))]
        else:
            rec = opt(EndOfLifeAction.RECYCLE, [_("It is retired and in Poor condition, so donating it would pass on a problem.")],
                      _("Recovers materials; check the recycler accepts this kind of item."), L.eol(EndOfLifeAction.RECYCLE))
            alts = [opt(EndOfLifeAction.DISASSEMBLE, [], _("Keeps working parts in use, but takes staff time."), no_workflow())]
        return Advice(asset, f, rec, alts + [dispose], estimates, rules)

    # 3. broken, or being repaired
    broken = f.state == AssetState.UNDER_MAINTENANCE or f.open_maintenance is not None or f.condition == Condition.POOR
    if broken:
        stop, why = _repair_not_worth_it(f)
        if stop:
            rec = opt(EndOfLifeAction.RECYCLE, why + [_("Recycling recovers the materials instead of spending more on repairs.")],
                      _("The item stops being usable; a reviewer must approve it first."), L.eol(EndOfLifeAction.RECYCLE))
            alts = [opt(EndOfLifeAction.DISASSEMBLE, [], _("Keeps working parts in use, but takes staff time."), no_workflow()),
                    opt(EndOfLifeAction.REPAIR, [], _("One more repair may work, but the rules above say it is unlikely to pay off."), L.report())]
            if good_enough:
                alts.insert(0, opt(EndOfLifeAction.DONATE, [], _("Someone may still use it as it is; it leaves the register."), L.eol(EndOfLifeAction.DONATE)))
            return Advice(asset, f, rec, alts + [dispose], estimates, rules)
        why = []
        if f.open_maintenance is not None or f.state == AssetState.UNDER_MAINTENANCE:
            why.append(_("A repair is already under way. Finishing it keeps the item in use."))
        else:
            why.append(_("It is in Poor condition. A repair usually costs less than buying new."))
        if f.value is None:
            why.append(_("The value is unknown, so the repair can't be checked against it; get a quote first."))
        rec = opt(EndOfLifeAction.REPAIR, why, _("Takes it out of use for about a week; costs money."), L.report())
        alts = [opt(EndOfLifeAction.RECYCLE, [], _("Only if the repair turns out too expensive or fails."), L.eol(EndOfLifeAction.RECYCLE))]
        return Advice(asset, f, rec, alts + [dispose], estimates, rules)

    # 4. not yet checked: confirm condition first
    if f.state in (AssetState.REGISTERED, AssetState.TRANSFERRED):
        rec = opt(EndOfLifeAction.RETAIN, [_("It hasn't been checked yet. Confirm its condition so it can be used or offered to others.")],
                  _("Nothing is offered to other units until it is checked."), L.our_assets(_("Confirm condition in Our assets"), "asset.custody"))
        return Advice(asset, f, rec, [], estimates, rules)

    # 5. available and working
    if f.demand_requests:
        why = [_("%(n)s request(s) for %(u)s unit(s) in this category are waiting in other units.") % {"n": f.demand_requests, "u": f.demand_units}]
        if f.published:
            why.append(_("It is already in the marketplace: approvers can match it to those requests."))
            link = (None, _("Nothing to do: requesters can already ask for it."))
        else:
            why.append(_("Publish it so those units can request it."))
            link = L.our_assets(_("Publish in Our assets"), "asset.publish")
        rec = opt(EndOfLifeAction.TRANSFER, why, _("Your unit no longer has it once the transfer is received."), link)
        alts = [opt(EndOfLifeAction.RETAIN, [], _("Keep it if your unit still uses it."), (None, _("No step needed.")))]
    else:
        why = [_("It works and nothing suggests a change.")]
        if f.published:
            why.append(_("It is listed for reuse, so any unit that needs one can ask for it."))
            link = (None, _("No step needed."))
        else:
            why.append(_("If your unit doesn't use it, publish it so another unit can."))
            link = L.our_assets(_("Publish in Our assets"), "asset.publish")
        rec = opt(EndOfLifeAction.RETAIN, why, _("Unused items still take space; listing them costs nothing."), link)
        alts = []
    if old and good_enough:
        alts.append(opt(EndOfLifeAction.DONATE, [_("It is %(y)s years old.") % {"y": f.age_months // 12}],
                        _("Frees space, but the university loses the item; prefer internal reuse first."), L.eol(EndOfLifeAction.DONATE)))
    if not f.published and not f.demand_requests:
        alts.append(opt(EndOfLifeAction.TRANSFER, [], _("Possible once it is published and another unit asks for it."), (None, _("Publish it first."))))
    return Advice(asset, f, rec, alts, estimates, rules)


def _estimates(f: Facts) -> list[Estimate]:
    """Figures from the existing formulas, each with how it was worked out. Missing inputs give no figure."""
    from .services import factor_for

    out = []
    if f.value is not None:
        out.append(Estimate(_("Buying one new"), _money(f.value),
                            _("The custodian's estimated value of one unit, used as the price of a new one.")))
        net_same, net_other = f.value - TRANSFER_COST_SAME_CAMPUS, f.value - TRANSFER_COST_OTHER_CAMPUS
        out.append(Estimate(_("Saved if one unit is reused instead"),
                            f"{_money(max(net_other, Decimal(0)))} – {_money(max(net_same, Decimal(0)))}",
                            _("Value minus the assumed transfer cost: %(o)s between campuses, %(s)s on the same campus.")
                            % {"o": _money(TRANSFER_COST_OTHER_CAMPUS), "s": _money(TRANSFER_COST_SAME_CAMPUS)}))
        if f.condition == Condition.POOR:
            out.append(Estimate(_("Next repair (assumed)"), _money(f.value * REPAIR_SHARE_POOR),
                                _("%(p)s%% of the value for a Poor item. An assumption, not a quote.") % {"p": int(REPAIR_SHARE_POOR * 100)}))
    if f.repairs:
        out.append(Estimate(_("Repairs recorded"), _money(f.repair_spent),
                            _("Sum of the costs entered on %(n)s repair record(s); %(k)s failed.") % {"n": f.repairs, "k": f.failed_repairs}))
    fac = factor_for(f.asset.category)
    if fac is not None:
        out.append(Estimate(_("Carbon of making one new"), f"{fac.kg_co2e_per_unit:,.0f} kg CO2e",
                            _("Locally selected carbon factor: %(src)s (%(d)s). Reuse avoids roughly this much per unit.")
                            % {"src": fac.source, "d": fac.source_date}))
    else:
        f.missing.append(_("Carbon factor: no locally selected factor covers this category, so no carbon figure is shown."))
    return out


def ai_profile(adv: Advice) -> dict:
    """What the AI may see: the facts and the rule result, no names of people (the gateway also strips them)."""
    f = adv.facts
    return {
        "item": {"category": f.asset.category.name, "state": f.state, "condition": f.condition, "age_months": f.age_months,
                 "value_aed": str(f.value) if f.value is not None else None, "repairs": f.repairs, "failed_repairs": f.failed_repairs,
                 "repair_spent_aed": str(f.repair_spent), "free_units": f.free, "published": f.published,
                 "waiting_requests_in_category": f.demand_requests},
        "rule_result": {"action": adv.recommended.action if adv.recommended else None,
                        "why": adv.recommended.why if adv.recommended else [],
                        "alternatives": [o.action for o in adv.alternatives]},
        "estimates": [{"label": e.label, "value": e.value, "how": e.how} for e in adv.estimates],
        "missing": f.missing,
    }


# ----------------------------------------------------------------------------- optional AI wording

def _numbers(text: str) -> set[str]:
    import re
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text or "")}


def explain_with_ai(user, asset: Asset, language: str = "en", gateway=None) -> dict:
    """Ask the AI gateway to re-word the rule-based advice. Returns a dict for the screen:
    {"ok", "text", "real" (a real model wrote it), "model", "status"}. Never raises on AI problems (NFR-26),
    and a reply with a number that is not in the input is discarded (rule 10)."""
    from apps.ai.gateway import AIGateway
    from apps.ai.models import ModelVersion
    from apps.common.errors import Forbidden

    if not can_advise(user, asset):
        raise Forbidden("Not permitted: sustainable-action advice")
    adv = recommend(user, asset)
    if adv.recommended is None:
        return {"ok": False, "status": "NONE"}
    payload = {**ai_profile(adv), "language": "ar" if language.startswith("ar") else "en"}
    result = (gateway or AIGateway()).recommend_action(payload, user)
    mv = ModelVersion.objects.filter(pk=result.model_version_id).first() if result.model_version_id else None
    text = (result.value or {}).get("text", "") if isinstance(result.value, dict) else ""
    out = {"ok": False, "status": result.status, "real": bool(mv and mv.provider != "fake"), "model": mv.model_name if mv else ""}
    if result.status not in ("OK", "LOW_CONFIDENCE") or not text:
        return out
    import json
    allowed = _numbers(json.dumps(payload, ensure_ascii=False, default=str))
    if not _numbers(text) <= allowed:
        out["status"] = "UNCHECKED_NUMBERS"
        return out
    out.update(ok=True, text=text[:1200])
    return out
