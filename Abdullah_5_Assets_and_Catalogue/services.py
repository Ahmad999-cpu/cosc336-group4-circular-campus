"""Public interface of the Assets & Catalogue module (features 4.1, 4.2, 4.4; lab C2 and C3).

Every function that changes data checks the permission for the asset's owning unit first, then calls the
Asset entity operations, which guard the state machine (Figure 7.5) and write history.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _l

from apps.access.models import Department, User
from apps.access.permissions import require, units_for
from apps.audit.services import record
from apps.common.enums import Condition
from apps.common.errors import Forbidden, ValidationFailed

from .models import Asset, AssetAttachment, AssetState, AssetTag, Category, PublicationStatus, TagSource

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DOC_TYPES = {"application/pdf"}
MAX_UPLOAD = 10 * 1024 * 1024


def clean_tags(raw) -> list[str]:
    """Comma-separated or list -> trimmed, de-duplicated (case-insensitive) tags of at most 60 characters."""
    return _clean_tags(raw)


def _clean_tags(raw) -> list[str]:
    if isinstance(raw, str):
        raw = raw.split(",")
    seen, out = set(), []
    for t in raw or []:
        t = " ".join(str(t).split())[:60]
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:12]


def _attach(asset: Asset, by: User, upload) -> AssetAttachment:
    ctype = getattr(upload, "content_type", "") or ""
    if ctype not in IMAGE_TYPES | DOC_TYPES:
        raise ValidationFailed("Upload a photo (JPG, PNG, WebP) or a PDF document")
    if upload.size > MAX_UPLOAD:
        raise ValidationFailed("Files can be at most 10 MB")
    n = (asset.attachments.order_by("-attachment_no").values_list("attachment_no", flat=True).first() or 0) + 1
    return AssetAttachment.objects.create(asset=asset, attachment_no=n, file=upload, file_type=ctype, uploaded_by=by)


@transaction.atomic
def register_asset(by: User, data: dict, *, uploads=(), tags=(), ai_tags=()) -> Asset:
    """UC-01 (C2). The asset starts Registered and unpublished; the custodian confirms its condition to make
    it Available (UC-12), then publishes it (UC-04)."""
    owner = data["owner_department"]
    require(by, "asset.register", owner)
    qty = int(data["quantity"]) if data.get("quantity") is not None else 1
    if qty < 1:
        raise ValidationFailed("Quantity must be at least 1")
    if data.get("estimated_value") is not None and Decimal(data["estimated_value"]) < 0:
        raise ValidationFailed("Value cannot be negative")
    if data.get("purchase_date") and data["purchase_date"] > date.today():
        raise ValidationFailed("Purchase date cannot be in the future")
    asset = Asset.objects.create(
        name=data["name"].strip(), description=data.get("description", ""), specifications=data.get("specifications", ""),
        category=data["category"], owner_department=owner, custodian=data.get("custodian") or by,
        quantity=qty, available_quantity=qty, reserved_quantity=0,
        location_campus=data["location_campus"], location_building=data.get("location_building", ""),
        location_room=data.get("location_room", ""), condition=data["condition"], purchase_date=data.get("purchase_date"),
        estimated_value=data.get("estimated_value"), serial_number=data.get("serial_number", ""),
        external_ref=data.get("external_ref", ""),
    )
    for t in _clean_tags(tags):
        AssetTag.objects.create(asset=asset, tag_text=t, source=TagSource.MANUAL)
    for t in _clean_tags(ai_tags):
        AssetTag.objects.get_or_create(asset=asset, tag_text=t, defaults={"source": TagSource.AI_ACCEPTED})
    for up in uploads:
        if up:
            _attach(asset, by, up)
    asset._emit("", by, "REGISTRATION", f"Registered {qty} unit(s) in {owner}")
    record(by, "register_asset", "Asset", asset.pk, after={"name": asset.name, "qty": qty, "owner": str(owner)})
    from apps.notifications.models import NotificationType
    from apps.notifications.services import Msg, enqueue
    if asset.custodian_id != by.pk:
        enqueue(asset.custodian, NotificationType.ASSET_REGISTERED, Msg(_l("%(name)s was registered with you as custodian."), name=asset.name),
                f"Asset:{asset.pk}", email=True)
    return asset


@transaction.atomic
def update_asset(by: User, asset: Asset, details: dict, *, uploads=(), tags=None) -> Asset:
    """UC-03. Only descriptive fields; state, quantities in use, owner and custodian change through workflows."""
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.register", asset.owner_department)
    changed = {k: v for k, v in details.items() if getattr(asset, k if k != "category" else "category_id") != (v.pk if k == "category" else v)}
    if changed:
        before = {k: str(getattr(asset, k)) for k in changed}
        asset.update(changed, by)
        record(by, "update_asset", "Asset", asset.pk, before=before, after={k: str(v) for k, v in changed.items()})
    if tags is not None:
        wanted = _clean_tags(tags)
        asset.tags.filter(source=TagSource.MANUAL).exclude(tag_text__in=wanted).delete()
        for t in wanted:
            AssetTag.objects.get_or_create(asset=asset, tag_text=t)
    for up in uploads:
        if up:
            _attach(asset, by, up)
    return asset


@transaction.atomic
def change_quantity(by: User, asset: Asset, quantity: int) -> Asset:
    """Correct a miscount. Never below the units already reserved or transferred out of this lot."""
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.register", asset.owner_department)
    if quantity < max(1, asset.reserved_quantity):
        raise ValidationFailed("Quantity cannot go below the units already reserved")
    diff = quantity - asset.quantity
    before = asset.quantity
    asset.quantity, asset.available_quantity = quantity, asset.available_quantity + diff
    asset._save("quantity", "available_quantity")
    asset._emit(asset.lifecycle_state, by, "UPDATE", f"Quantity corrected from {before} to {quantity}")
    record(by, "change_quantity", "Asset", asset.pk, before={"quantity": before}, after={"quantity": quantity})
    return asset


@transaction.atomic
def confirm_condition(by: User, asset: Asset, condition: str) -> Asset:
    """UC-12: the custodian checks the item and confirms it can be reused. Registered or Transferred -> Available."""
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.custody", asset.owner_department)
    if condition != asset.condition:
        asset.update_condition(condition, by)
    if asset.lifecycle_state in (AssetState.REGISTERED, AssetState.TRANSFERRED):
        asset.mark_available(by)
    return asset


@transaction.atomic
def publish(by: User, asset: Asset) -> Asset:
    """UC-04 (C3). Only Available assets with free units (BR-3)."""
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.publish", asset.owner_department)
    asset.publish(by)
    if asset.expected_available_on is not None:  # Phase 6: the coming-soon item is now really available
        asset.clear_expected(by, ready=True)
    record(by, "publish_asset", "Asset", asset.pk)
    return asset


# ---------- Phase 6: coming soon ----------

@transaction.atomic
def set_expected_date(by: User, asset: Asset, when, note: str = "") -> Asset:
    """List an item as coming soon. The date is a plan, not a promise: the item can only be requested once the
    custodian confirms its condition and publishes it."""
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.publish", asset.owner_department)
    before = asset.expected_available_on
    asset.set_expected(when, note, by)
    record(by, "set_expected_date", "Asset", asset.pk, before={"date": str(before) if before else None}, after={"date": str(when)})
    return asset


@transaction.atomic
def cancel_expected_date(by: User, asset: Asset, reason: str = "") -> Asset:
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.publish", asset.owner_department)
    if asset.expected_available_on is None:
        raise ValidationFailed("This item is not listed as coming soon")
    before = asset.expected_available_on
    asset.clear_expected(by, reason)
    record(by, "cancel_expected_date", "Asset", asset.pk, before={"date": str(before)}, after={"reason": reason[:200]})
    return asset


def upcoming():
    """What Browse lists as coming soon (visible to everyone signed in)."""
    return (Asset.objects.filter(expected_available_on__isnull=False, lifecycle_state__in=Asset.UPCOMING_FROM)
            .exclude(publication_status=PublicationStatus.PUBLISHED))


@transaction.atomic
def unpublish(by: User, asset: Asset) -> Asset:
    """UC-05. Refused while units are reserved (no commitments)."""
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    require(by, "asset.publish", asset.owner_department)
    asset.unpublish(by)
    record(by, "unpublish_asset", "Asset", asset.pk)
    return asset


# ---------- reading ----------

SORTS = {
    "units": (F("available_quantity") - F("reserved_quantity")).desc(),
    "value": F("estimated_value").desc(nulls_last=True),
    "newest": F("created_at").desc(),
    "name": F("name").asc(),
}


def published():
    """What the marketplace shows: published, reservable, with at least one free unit."""
    return (Asset.objects.filter(publication_status=PublicationStatus.PUBLISHED,
                                 lifecycle_state__in=[AssetState.AVAILABLE, AssetState.RESERVED])
            .filter(available_quantity__gt=F("reserved_quantity")))


def search(qs=None, *, q="", category=None, condition="", department=None, campus="", min_free=None,
           max_age_years=None, max_value=None, state="", sort="units"):
    """Classic search (UC-20 to UC-22): case-insensitive keyword match plus AND filters (Section 9.10).
    Meaning-based search is the Matching module's job."""
    qs = published() if qs is None else qs
    if q:
        for word in q.split()[:6]:
            qs = qs.filter(Q(name__icontains=word) | Q(description__icontains=word) | Q(specifications__icontains=word)
                           | Q(tags__tag_text__icontains=word) | Q(serial_number__iexact=word)
                           | Q(owner_department__name__icontains=word))
    if category:
        qs = qs.filter(category_id__in=category.descendant_ids())
    if condition:
        qs = qs.filter(condition=condition)
    if department:
        ids = {department.pk} | {d.pk for d in Department.objects.all() if d.is_within(department)}
        qs = qs.filter(owner_department_id__in=ids)
    if campus:
        qs = qs.filter(location_campus=campus)
    if min_free:
        qs = qs.filter(available_quantity__gte=F("reserved_quantity") + int(min_free))
    if max_age_years:
        qs = qs.filter(purchase_date__gte=date.today() - timedelta(days=365 * int(max_age_years)))
    if max_value:
        qs = qs.filter(estimated_value__lte=max_value)
    if state:
        qs = qs.filter(lifecycle_state=state)
    return (qs.distinct().select_related("category", "owner_department", "custodian")
            .prefetch_related("attachments", "tags").order_by(SORTS.get(sort, SORTS["units"]), "name"))


WORKS_WITH = ("asset.register", "maintenance.record", "eol.approve", "request.approve", "transfer.dispatch")


def can_view(user: User, asset: Asset) -> bool:
    """Published items are visible to everyone signed in; unpublished ones to the custodian and to people who
    work with that unit's items (register, maintain, approve, dispatch). Found in validation: maintenance staff
    were sent to a 404 for items under repair."""
    if asset.publication_status == PublicationStatus.PUBLISHED or asset.custodian_id == user.pk or asset.is_upcoming:
        return True  # Phase 6: a coming-soon listing is meant to be discovered
    from apps.access.permissions import can
    return any(can(user, action, asset.owner_department) for action in WORKS_WITH)


LABELLERS = ("asset.register", "asset.custody", "maintenance.record")
GONE_STATES = (AssetState.DONATED, AssetState.RECYCLED, AssetState.DISPOSED)


def can_label(user: User, asset: Asset) -> bool:
    """Feature 1: who may show, print or download an asset's QR label: its custodian and the people who register,
    hold custody of or maintain that unit's items. Everyone else simply scans it."""
    if not getattr(user, "is_authenticated", False):
        return False
    if asset.custodian_id == user.pk:
        return True
    from apps.access.permissions import can
    return any(can(user, action, asset.owner_department) for action in LABELLERS)


def require_label(user: User, asset: Asset) -> None:
    if not can_label(user, asset):
        raise Forbidden("Not permitted: asset labels")
    if asset.lifecycle_state in GONE_STATES:
        raise ValidationFailed("This asset has left the register (donated, recycled or disposed), so it gets no new label")


def managed_by(user: User):
    """Assets in the units where `user` may register assets (the 'Our assets' console)."""
    units = units_for(user, "asset.register")
    return Asset.objects.filter(owner_department__in=units)


def campuses() -> list[str]:
    return list(Asset.objects.order_by().values_list("location_campus", flat=True).distinct())


def top_categories():
    return Category.objects.filter(parent__isnull=True).order_by("name")


# ----------------------------------------------------------------------------- AI feature 1 (optional)

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AI_IMAGE = 5 * 1024 * 1024


def suggest_details(by: User, data: dict, photo=None, gateway=None) -> dict:
    """AI 1: suggest category, tags, a standard description and the serial number from the text and, if given,
    a photo. Suggestions are never applied automatically; low confidence is shown as "not sure" (FR-11.21)."""
    from apps.ai.gateway import AIGateway  # catalogue sits below ai in the import order; import late
    require_any = units_for(by, "asset.register")
    if not require_any.exists():
        raise Forbidden("Not permitted: asset.register")
    text = {k: (data.get(k) or "").strip()[:2000] for k in ("name", "description", "specifications", "serial_number")}
    if not any(text.values()) and photo is None:
        raise ValidationFailed("Type a name or add a photo first")
    cats = list(Category.objects.select_related("parent").order_by("name"))
    payload = {**text, "categories": [c.path() for c in cats]}
    if photo is not None and getattr(photo, "content_type", "") in IMAGE_TYPES and photo.size <= MAX_AI_IMAGE:
        import base64
        photo.seek(0)
        payload["image"] = {"media_type": photo.content_type, "data": base64.b64encode(photo.read()).decode()}
        photo.seek(0)
    result = (gateway or AIGateway()).classify(payload, by)
    out = {"status": result.status, "ok": result.ok, "inference_id": result.inference_id, "confidence": result.confidence,
           "low": result.status == "LOW_CONFIDENCE", "used_photo": "image" in payload}
    if not result.ok or not isinstance(result.value, dict):
        return out
    v = result.value
    by_path = {c.path().lower(): c for c in cats}
    by_name = {c.name.lower(): c for c in cats}
    wanted = [str(v.get(k) or "").strip().lower() for k in ("subcategory", "category")]
    out["category"] = next((by_path.get(w) or by_name.get(w) or by_name.get(w.split("/")[-1].strip())
                            for w in wanted if w and (by_path.get(w) or by_name.get(w) or by_name.get(w.split("/")[-1].strip()))), None)
    out["tags"] = [t for t in _clean_tags(",".join(str(t) for t in (v.get("tags") or [])[:8]))]
    out["description"] = str(v.get("standardDescription") or "").strip()[:500]
    out["serial_number"] = str(v.get("serialNumber") or "").strip()[:100]
    cond = str(v.get("conditionGuess") or "").upper()
    out["condition"] = cond if cond in Condition.values else ""
    out["missing"] = [str(m) for m in (v.get("missingFields") or [])][:6]
    return out


# ---------- Phase 7: questions on an asset ----------

ANSWERERS = ("asset.register", "asset.custody")
MAX_OPEN_PER_ASKER = 3
STALE_DAYS = 14


def can_answer(user: User, asset: Asset) -> bool:
    from apps.access.permissions import can
    return asset.custodian_id == user.pk or any(can(user, p, asset.owner_department) for p in ANSWERERS)


def can_ask(user: User, asset: Asset) -> bool:
    return (getattr(user, "is_authenticated", False) and can_view(user, asset) and not can_answer(user, asset)
            and asset.lifecycle_state not in GONE_STATES + (AssetState.RETIRED,))


def _text(raw, limit: int, what: str) -> str:
    t = " ".join((raw or "").split())
    if len(t) < 3 and what == "q":
        raise ValidationFailed("Write a question of at least 3 characters")
    if len(t) < 3:
        raise ValidationFailed("Write an answer of at least 3 characters")
    if len(t) > limit and what == "q":
        raise ValidationFailed("Keep questions under 500 characters")
    if len(t) > limit:
        raise ValidationFailed("Keep answers under 1,000 characters")
    return t


@transaction.atomic
def ask_question(by: User, asset: Asset, text: str):
    from apps.notifications.models import NotificationType
    from apps.notifications.services import Msg, enqueue

    from .models import AssetQuestion
    asset = Asset.objects.select_related("custodian", "owner_department").get(pk=asset.pk)  # decide on the current row
    if not can_view(by, asset):
        raise Forbidden("Not permitted: this asset")
    if can_answer(by, asset):
        raise ValidationFailed("You look after this item; answer questions instead of asking them")
    if asset.lifecycle_state in GONE_STATES + (AssetState.RETIRED,):
        raise ValidationFailed("This item has left the register, so it takes no new questions")
    t = _text(text, AssetQuestion.QUESTION_MAX, "q")
    if AssetQuestion.objects.filter(asset=asset, asked_by=by, answered_at__isnull=True).count() >= MAX_OPEN_PER_ASKER:
        raise ValidationFailed("You already have 3 unanswered questions on this item. Wait for an answer first")
    q = AssetQuestion.objects.create(asset=asset, asked_by=by, asker_unit=by.department, text=t)
    enqueue(asset.custodian, NotificationType.ASSET_QUESTION,
            Msg(_l("New question about %(name)s: \"%(q)s\""), name=asset.name, q=t[:80]), f"Asset:{asset.pk}", email=True)
    record(by, "ask_question", "AssetQuestion", q.pk, after={"asset": str(asset.pk)})
    return q


@transaction.atomic
def answer_question(by: User, question, text: str):
    from apps.notifications.models import NotificationType
    from apps.notifications.services import Msg, enqueue

    from .models import AssetQuestion
    q = AssetQuestion.objects.select_for_update().select_related("asset").get(pk=question.pk)
    if not can_answer(by, q.asset):
        raise Forbidden("Only the item's custodian can answer")
    if q.is_closed:
        raise ValidationFailed("This item has left the register; the question is closed")
    first = not q.is_answered
    q.answer, q.answered_by, q.answered_at = _text(text, AssetQuestion.ANSWER_MAX, "a"), by, timezone.now()
    q.save(update_fields=["answer", "answered_by", "answered_at"])
    enqueue(q.asked_by, NotificationType.ASSET_ANSWER,
            Msg(_l("Your question about %(name)s was answered.") if first else _l("The answer to your question about %(name)s was updated."),
                name=q.asset.name), f"Asset:{q.asset_id}")
    record(by, "answer_question", "AssetQuestion", q.pk, after={"edited": not first})
    return q


@transaction.atomic
def withdraw_question(by: User, question) -> None:
    from .models import AssetQuestion
    q = AssetQuestion.objects.select_for_update().get(pk=question.pk)
    if q.asked_by_id != by.pk:
        raise Forbidden("Only the person who asked can withdraw a question")
    if q.is_answered:
        raise ValidationFailed("Answered questions stay on the item for others to read")
    q.delete()


def questions_for_asset(asset: Asset):
    return asset.questions.select_related("asked_by", "asker_unit", "answered_by")


def questions_to_answer(user: User):
    """Unanswered questions on items this person looks after, oldest first."""
    from django.db.models import Q

    from .models import AssetQuestion
    units = units_for(user, "asset.register") | units_for(user, "asset.custody")
    return (AssetQuestion.objects.filter(answered_at__isnull=True)
            .filter(Q(asset__custodian=user) | Q(asset__owner_department__in=units))
            .exclude(asset__lifecycle_state__in=GONE_STATES).select_related("asset", "asked_by", "asker_unit").order_by("asked_at").distinct())


def unanswered_count(user: User) -> int:
    return questions_to_answer(user).count()
