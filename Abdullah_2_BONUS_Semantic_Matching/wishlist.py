"""Phase 5: saved needs (wishlist) and availability alerts.

A person saves a need when nothing suitable is free. Whenever an item is published, or a published item gets free
units again, the active needs are scored against it with the same MatchingEngine as Find (hard rules, embeddings,
eight factors, explanation). A suitable match is notified once; the same unchanged match is never notified again.
A notification links to the item; it never requests or reserves anything.

Phase 6 adds "interest" needs tied to one coming-soon item (`SavedNeed.asset`): those are told when that item is
published, whatever the score, and when its expected date changes or is cancelled.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from apps.access.models import User
from apps.access.permissions import require
from apps.catalogue.models import Asset
from apps.catalogue.services import published
from apps.common.errors import Forbidden, ValidationFailed
from apps.notifications.models import NotificationType
from apps.notifications.services import Msg, enqueue

from .embeddings import cosine, get_embedder
from .engine import MatchingEngine, Need
from .models import SUITABLE_SCORE, WEAK_SCORE, NeedMatch, NeedStatus, SavedNeed

log = logging.getLogger(__name__)
MAX_ACTIVE = 20          # per person: keeps the per-publication check small
FIELDS = ("description", "category", "quantity", "specifications", "preferred_condition", "campus", "needed_by")


# ----------------------------------------------------------------------------- the person's own needs

def mine(user: User):
    return SavedNeed.objects.filter(owner=user).select_related("category", "asset")


def _own(user: User, need: SavedNeed) -> SavedNeed:
    if need.owner_id != user.pk:
        raise Forbidden("Only the person who saved this need can change it")
    return need


def _clean(data: dict) -> dict:
    d = {k: data.get(k) for k in FIELDS if k in data}
    if "description" in d:
        d["description"] = (d["description"] or "").strip()
        if len(d["description"]) < 3:
            raise ValidationFailed("Describe what you need in a few words")
        if len(d["description"]) > 300:
            raise ValidationFailed("Keep the description under 300 characters")
    if "quantity" in d and not (1 <= int(d["quantity"] or 0) <= 999):
        raise ValidationFailed("Quantity must be between 1 and 999")
    if d.get("needed_by") and d["needed_by"] < timezone.localdate():
        raise ValidationFailed("The needed-by date is in the past")
    d["preferred_condition"] = d.get("preferred_condition") or "ANY"
    return d


@transaction.atomic
def save_need(user: User, data: dict) -> tuple[SavedNeed, list[NeedMatch]]:
    """Create a need and show what already fits (recorded as seen, so it is not notified later)."""
    dept = user.department
    require(user, "request.submit", dept)
    if mine(user).filter(status=NeedStatus.ACTIVE, asset__isnull=True).count() >= MAX_ACTIVE:
        raise ValidationFailed("You have 20 active saved needs. Deactivate or delete one first")
    need = SavedNeed.objects.create(owner=user, department=dept, **_clean(data))
    return need, check_need(need, notify=False)


@transaction.atomic
def update_need(user: User, need: SavedNeed, data: dict) -> tuple[SavedNeed, list[NeedMatch]]:
    need = _own(user, SavedNeed.objects.select_for_update().get(pk=need.pk))
    for k, v in _clean(data).items():
        setattr(need, k, v)
    need.save()
    need.matches.all().delete()  # the need changed, so earlier matches no longer describe it
    return need, check_need(need, notify=False)


def set_active(user: User, need: SavedNeed, active: bool) -> SavedNeed:
    need = _own(user, need)
    need.status = NeedStatus.ACTIVE if active else NeedStatus.INACTIVE
    need.save(update_fields=["status", "updated_at"])
    return need


def delete_need(user: User, need: SavedNeed) -> None:
    _own(user, need).delete()


# ----------------------------------------------------------------------------- matching

def _need(n: SavedNeed) -> Need:
    return Need(text=n.description, specs=n.specifications, quantity=n.quantity, preferred_condition=n.preferred_condition,
                campus=n.campus or (n.department.campus or ""), required_date=n.needed_by)


def _candidates(n: SavedNeed, assets=None):
    """The same hard rules as Find, but at least one free unit is enough (a partial match is shown as partial)."""
    qs = published().exclude(owner_department_id=n.department_id).select_related("category", "owner_department")
    if n.category_id:
        qs = qs.filter(category_id__in=n.category.descendant_ids())
    if assets is not None:
        qs = qs.filter(pk__in=[a.pk for a in assets])
    return [a for a in qs if a.unreserved_quantity > 0]


@dataclass
class Scored:
    asset: Asset
    score: float
    explanation: str


def _score(n: SavedNeed, assets) -> list[Scored]:
    from .services import _emission_kg, asset_text
    if not assets:
        return []
    emb = get_embedder()
    need = _need(n)
    vectors = emb.embed([need.text + " " + need.specs] + [asset_text(a) for a in assets])
    engine = MatchingEngine(emb.name)
    out = []
    for a, v in zip(assets, vectors[1:]):
        c = engine.factors(need, a, cosine(vectors[0], v), _emission_kg(a.category))
        if c is None:
            continue
        ranked = engine.rank([c], need.urgency, keep_below=WEAK_SCORE)
        if ranked:
            out.append(Scored(a, ranked[0].score, ranked[0].explanation))
    return out


def _signature(n: SavedNeed, a: Asset, score: float) -> str:
    """What the person is told: covered units, condition, score band of 10. Unchanged = not notified again."""
    return f"{min(a.unreserved_quantity, n.quantity)}:{a.condition}:{int(score // 10)}"


def _notify(n: SavedNeed, m: NeedMatch) -> None:
    if n.is_interest:
        msg = Msg(_l("%(name)s is now available. You asked to be told; request it if you still need it."), name=m.asset.name)
    elif m.partial:
        msg = Msg(_l("%(name)s may fit your saved need \"%(need)s\", but only %(c)s of %(q)s units are free."),
                  name=m.asset.name, need=n.description[:60], c=m.covered, q=n.quantity)
    else:
        msg = Msg(_l("%(name)s may fit your saved need \"%(need)s\" (score %(s)s of 100)."),
                  name=m.asset.name, need=n.description[:60], s=f"{m.score:.0f}")
    enqueue(n.owner, NotificationType.NEED_MATCH, msg, f"Asset:{m.asset_id}", email=True)
    m.notified_signature, m.notified_at = m.signature, timezone.now()
    m.save(update_fields=["notified_signature", "notified_at", "updated_at"])


def check_need(n: SavedNeed, assets=None, notify: bool = True) -> list[NeedMatch]:
    """Score this need against published items (all, or the given ones). Records matches; notifies new or
    changed suitable ones when `notify`. If matching fails, the need is flagged and nothing else changes."""
    if n.status != NeedStatus.ACTIVE:
        return []
    try:
        if n.is_interest:
            cands = [a for a in _candidates(n, [n.asset] if assets is None else assets) if a.pk == n.asset_id]
            scored = [Scored(a, 100.0, _("The item you asked to hear about is now available.")) for a in cands]
        else:
            scored = _score(n, _candidates(n, assets))
    except Exception as exc:  # embeddings or model unavailable: try again at the next publication or "Check now"
        log.warning("Saved-need check failed for %s: %s", n.pk, exc)
        SavedNeed.objects.filter(pk=n.pk).update(check_failed=True, last_checked_at=timezone.now())
        n.check_failed = True
        return []
    out = []
    for s in scored:
        sig = _signature(n, s.asset, s.score)
        m, _created = NeedMatch.objects.update_or_create(
            need=n, asset=s.asset, defaults={"score": Decimal(str(s.score)), "covered": min(s.asset.unreserved_quantity, n.quantity),
                                             "explanation": s.explanation, "signature": sig})
        m.need, m.asset = n, s.asset
        if not notify and not m.notified_signature:
            m.notified_signature = sig  # shown on screen when saved: counts as told
            m.save(update_fields=["notified_signature"])
        elif notify and s.score >= SUITABLE_SCORE and m.notified_signature != sig:
            _notify(n, m)
        out.append(m)
    SavedNeed.objects.filter(pk=n.pk).update(check_failed=False, last_checked_at=timezone.now())
    n.check_failed = False
    return out


def check_asset(asset: Asset) -> int:
    """Called after an item is published or gets free units again. Returns how many people were notified."""
    asset = Asset.objects.select_related("category", "owner_department").get(pk=asset.pk)
    if not published().filter(pk=asset.pk).exists():
        return 0
    told = 0
    needs = (SavedNeed.objects.filter(status=NeedStatus.ACTIVE).exclude(department_id=asset.owner_department_id)
             .select_related("owner", "department", "category", "asset"))
    for n in needs:
        if n.is_interest and n.asset_id != asset.pk:
            continue
        before = n.matches.filter(asset=asset).values_list("notified_signature", flat=True).first()
        for m in check_need(n, [asset], notify=True):
            if m.notified_signature and m.notified_signature != before and (m.score >= SUITABLE_SCORE):
                told += 1
    return told


def current_matches(n: SavedNeed):
    """Matches still worth showing: the item is still published with free units."""
    ids = set(published().values_list("pk", flat=True))
    return [m for m in n.matches.select_related("asset", "asset__owner_department", "asset__category") if m.asset_id in ids
            and m.asset.unreserved_quantity > 0]



# ----------------------------------------------------------------------------- Phase 6: interest in a coming-soon item

@transaction.atomic
def express_interest(user: User, asset: Asset) -> SavedNeed:
    """'Tell me when it's ready'. Interest only: no request, no reservation, no place in a queue."""
    require(user, "request.submit", user.department)
    asset = Asset.objects.select_related("category").get(pk=asset.pk)
    if not asset.is_upcoming:
        raise ValidationFailed("This item is not listed as coming soon")
    if asset.owner_department_id == user.department_id:
        raise ValidationFailed("This item already belongs to your unit")
    need, _created = SavedNeed.objects.get_or_create(
        owner=user, asset=asset, defaults={"department": user.department, "description": asset.name[:300],
                                           "category": asset.category, "quantity": 1})
    if need.status != NeedStatus.ACTIVE:
        need.status = NeedStatus.ACTIVE
        need.save(update_fields=["status", "updated_at"])
    return need


def availability_changed(asset: Asset, kind: str, before, after) -> int:
    """The custodian set, moved or cancelled the expected date: tell everyone who asked about this item.
    ('ready' is handled by the publication check, which sends the 'now available' message.)"""
    if kind not in ("changed", "cancelled"):
        return 0
    told = 0
    for n in SavedNeed.objects.filter(asset=asset, status=NeedStatus.ACTIVE).select_related("owner"):
        if kind == "changed":
            msg = Msg(_l("%(name)s is now expected from %(d)s (was %(b)s). It still can't be requested until it is ready."),
                      name=asset.name, d=after.strftime("%d %b %Y"), b=before.strftime("%d %b %Y"))
        else:
            msg = Msg(_l("%(name)s is no longer listed as coming soon. Your interest has been closed; save a need to keep looking."),
                      name=asset.name)
            n.status = NeedStatus.INACTIVE
            n.save(update_fields=["status", "updated_at"])
        enqueue(n.owner, NotificationType.AVAILABILITY, msg, f"Asset:{asset.pk}")
        told += 1
    return told
