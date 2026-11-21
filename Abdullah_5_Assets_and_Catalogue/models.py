"""Assets & Catalogue module (features 4.1 registration, 4.2 publication, 4.4 search; stores 4.3 AI tags).

Classes: Category, Asset, AssetAttachment, AssetTag.
Asset operations implement the asset state machine (Figure 7.5) and BR-7 (reserved <= available).
Every state change emits `asset_history` so the Life Cycle module writes a LifeCycleEvent in the same
transaction (BR-10, NFR-27) without this module importing it.
"""
from datetime import date

from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import Department, User
from apps.common.enums import Condition
from apps.common.errors import InsufficientQuantity, ValidationFailed
from apps.common.models import Location, UUIDModel
from apps.common.statemachine import move

from .signals import asset_history


class Category(UUIDModel):
    name = models.CharField(max_length=120)
    name_ar = models.CharField(max_length=120, blank=True)
    material_type = models.CharField(max_length=80, blank=True)
    icon = models.CharField(max_length=20, default="box", help_text=_("Icon name from apps/web/templatetags/ui.py"))
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.path()

    @property
    def display_name(self) -> str:
        from django.utils.translation import get_language
        return self.name_ar if self.name_ar and (get_language() or "").startswith("ar") else self.name

    def add_child(self, c: "Category") -> None:
        c.parent = self
        c.save(update_fields=["parent"])

    def path(self) -> str:
        parts, node = [self.name], self.parent
        while node is not None:
            parts.append(node.name)
            node = node.parent
        return " / ".join(reversed(parts))

    def descendant_ids(self) -> set:
        ids, frontier = {self.pk}, [self.pk]
        while frontier:
            frontier = list(Category.objects.filter(parent_id__in=frontier).values_list("pk", flat=True))
            ids.update(frontier)
        return ids


class AssetState(models.TextChoices):
    REGISTERED = "REGISTERED", _("Registered")
    AVAILABLE = "AVAILABLE", _("Available")
    RESERVED = "RESERVED", _("Reserved")
    TRANSFERRED = "TRANSFERRED", _("Transferred")
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE", _("Under maintenance")
    RETIRED = "RETIRED", _("Retired")
    DONATED = "DONATED", _("Donated")
    RECYCLED = "RECYCLED", _("Recycled")
    DISPOSED = "DISPOSED", _("Disposed")


# Figure 7.5. Guards are enforced in the operations below.
ASSET_TRANSITIONS = {
    AssetState.REGISTERED: {AssetState.AVAILABLE, AssetState.UNDER_MAINTENANCE},
    AssetState.AVAILABLE: {AssetState.RESERVED, AssetState.UNDER_MAINTENANCE, AssetState.RETIRED},
    AssetState.RESERVED: {AssetState.AVAILABLE, AssetState.TRANSFERRED},
    AssetState.TRANSFERRED: {AssetState.AVAILABLE},
    AssetState.UNDER_MAINTENANCE: {AssetState.AVAILABLE, AssetState.RETIRED},
    AssetState.RETIRED: {AssetState.DONATED, AssetState.RECYCLED, AssetState.DISPOSED},
    AssetState.DONATED: set(),
    AssetState.RECYCLED: set(),
    AssetState.DISPOSED: set(),
}
END_OF_LIFE_STATES = {AssetState.RETIRED, AssetState.DONATED, AssetState.RECYCLED, AssetState.DISPOSED}


class PublicationStatus(models.TextChoices):
    UNPUBLISHED = "UNPUBLISHED", _("Unpublished")
    PUBLISHED = "PUBLISHED", _("Published")


class Asset(UUIDModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    specifications = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="assets")
    owner_department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="assets")
    custodian = models.ForeignKey(User, on_delete=models.PROTECT, related_name="custody_assets")

    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    reserved_quantity = models.PositiveIntegerField(default=0)

    location_campus = models.CharField(max_length=100)
    location_building = models.CharField(max_length=100, blank=True)
    location_room = models.CharField(max_length=50, blank=True)

    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.GOOD)
    purchase_date = models.DateField(null=True, blank=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                          help_text=_("Estimated value of ONE unit, in AED"))
    lifecycle_state = models.CharField(max_length=20, choices=AssetState.choices, default=AssetState.REGISTERED, editable=False)
    publication_status = models.CharField(max_length=12, choices=PublicationStatus.choices, default=PublicationStatus.UNPUBLISHED, editable=False)
    row_version = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additions for the pilot (not in the Phase 5 class diagram): imported registers and photo auto-capture.
    serial_number = models.CharField(max_length=120, blank=True)
    external_ref = models.CharField(max_length=120, blank=True, help_text=_("ID in the institution's existing register (e.g. BMC, SAP)"))

    # Phase 6: listed as "coming soon". Set and cleared only through set_expected / clear_expected.
    expected_available_on = models.DateField(null=True, blank=True, editable=False)
    upcoming_note = models.CharField(max_length=200, blank=True, editable=False)

    class Meta:
        constraints = [
            # BR-7 as database constraints, so even a bug in a service cannot over-allocate.
            models.CheckConstraint(condition=Q(reserved_quantity__lte=F("available_quantity")), name="asset_reserved_lte_available"),
            models.CheckConstraint(condition=Q(available_quantity__lte=F("quantity")), name="asset_available_lte_quantity"),
        ]
        indexes = [models.Index(fields=["lifecycle_state", "publication_status"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.quantity})"

    @property
    def photo(self):
        """First image attachment, or None (cards then show the category icon)."""
        for att in self.attachments.all():
            if att.file_type.startswith("image/"):
                return att
        return None

    # --- derived ---
    @property
    def location(self) -> Location:
        return Location(self.location_campus, self.location_building, self.location_room)

    @property
    def unreserved_quantity(self) -> int:
        return self.available_quantity - self.reserved_quantity

    def age(self, today: date | None = None):
        """/assetAge: whole months since purchase, or None if the purchase date is unknown."""
        if not self.purchase_date:
            return None
        t = today or timezone.localdate()
        return (t.year - self.purchase_date.year) * 12 + (t.month - self.purchase_date.month)

    # --- internal ---
    def _save(self, *fields: str) -> None:
        self.row_version += 1
        self.save(update_fields=[*fields, "row_version", "updated_at"])

    def _emit(self, previous: str, by: User, event_type: str, description: str = "", **extra) -> None:
        asset_history.send(sender=Asset, asset=self, previous_state=previous, new_state=self.lifecycle_state,
                           by=by, event_type=event_type, description=description, **extra)

    # --- class diagram operations ---
    EDITABLE_FIELDS = ("name", "description", "specifications", "category", "location_campus", "location_building",
                       "location_room", "purchase_date", "estimated_value", "serial_number", "external_ref")

    def update(self, details: dict, by: User) -> None:
        """Generic edit. Cannot touch state, quantities in use, custody or owner (FR-2.16)."""
        bad = set(details) - set(self.EDITABLE_FIELDS)
        if bad:
            raise ValidationFailed(f"Fields not editable here: {', '.join(sorted(bad))}")
        for k, v in details.items():
            setattr(self, k, v)
        self._save(*details.keys())
        self._emit(self.lifecycle_state, by, "UPDATE", f"Edited: {', '.join(details)}")

    def change_state(self, to: str, by: User, *, description: str = "", approval_ref=None, source=None) -> None:
        """Move along Figure 7.5. End-of-life states need an approved EndOfLifeProposal (BR-11)."""
        if to in END_OF_LIFE_STATES and approval_ref is None:
            raise ValidationFailed("End-of-life states need an approved proposal reference")
        if to == AssetState.UNDER_MAINTENANCE and self.reserved_quantity > 0:
            raise ValidationFailed("Cannot start maintenance while units are reserved")
        previous = move(self, "lifecycle_state", to, ASSET_TRANSITIONS)
        fields = ["lifecycle_state"]
        if to not in (AssetState.AVAILABLE, AssetState.RESERVED) and self.publication_status == PublicationStatus.PUBLISHED:
            self.publication_status = PublicationStatus.UNPUBLISHED  # leaving the marketplace
            fields.append("publication_status")
        self._save(*fields)
        self._emit(previous, by, "STATE_CHANGE", description, approval_ref=approval_ref, source=source)

    # --- Phase 6: future availability ---
    UPCOMING_FROM = (AssetState.REGISTERED, AssetState.AVAILABLE, AssetState.UNDER_MAINTENANCE, AssetState.TRANSFERRED)

    @property
    def is_upcoming(self) -> bool:
        """Listed as coming soon: has an expected date, is not in the marketplace yet, and is still in use."""
        return (self.expected_available_on is not None and self.publication_status != PublicationStatus.PUBLISHED
                and self.lifecycle_state in self.UPCOMING_FROM)

    @property
    def is_overdue(self) -> bool:
        return self.is_upcoming and self.expected_available_on < timezone.localdate()

    def set_expected(self, when: date, note: str, by: User) -> None:
        if self.publication_status == PublicationStatus.PUBLISHED:
            raise ValidationFailed("It is already available now; unpublish it first to give a future date")
        if self.lifecycle_state not in self.UPCOMING_FROM:
            raise ValidationFailed("Items at the end of their life can't be listed as coming soon")
        if when <= timezone.localdate():
            raise ValidationFailed("Pick a date after today. If it is ready now, confirm its condition and publish it")
        before = self.expected_available_on
        self.expected_available_on, self.upcoming_note = when, note.strip()[:200]
        self._save("expected_available_on", "upcoming_note")
        kind = "changed" if before else "set"
        text = f"Expected available from {when:%Y-%m-%d}" + (f" (was {before:%Y-%m-%d})" if before else "")
        self._emit(self.lifecycle_state, by, "UPDATE", text, availability=(kind, before, when))

    def clear_expected(self, by: User, reason: str = "", *, ready: bool = False) -> None:
        if self.expected_available_on is None:
            return
        before = self.expected_available_on
        self.expected_available_on, self.upcoming_note = None, ""
        self._save("expected_available_on", "upcoming_note")
        text = "Coming-soon listing ended: now available" if ready else "Coming-soon listing cancelled" + (f": {reason.strip()}" if reason.strip() else "")
        self._emit(self.lifecycle_state, by, "UPDATE", text, availability=("ready" if ready else "cancelled", before, None))

    def mark_available(self, by: User) -> None:
        """Condition confirmed by the custodian (UC-12)."""
        self.change_state(AssetState.AVAILABLE, by, description="Condition confirmed")

    def update_condition(self, c: str, by: User) -> None:
        self.condition = c
        self._save("condition")
        self._emit(self.lifecycle_state, by, "CONDITION_UPDATE", f"Condition set to {c}")

    def is_publishable(self) -> bool:
        return self.lifecycle_state == AssetState.AVAILABLE and self.unreserved_quantity > 0

    def publish(self, by: User) -> None:
        if self.publication_status == PublicationStatus.PUBLISHED:
            return
        if not self.is_publishable():
            raise ValidationFailed("Only available assets with free units can be published (BR-3)")
        self.publication_status = PublicationStatus.PUBLISHED
        self._save("publication_status")
        self._emit(self.lifecycle_state, by, "PUBLICATION", "Published")

    def unpublish(self, by: User) -> None:
        if self.reserved_quantity > 0:
            raise ValidationFailed("Cannot unpublish while units are reserved")
        self.publication_status = PublicationStatus.UNPUBLISHED
        self._save("publication_status")
        self._emit(self.lifecycle_state, by, "PUBLICATION", "Unpublished")

    def allocate(self, qty: int, by: User) -> None:
        """Reserve units on approval. Call only on a row locked with select_for_update (BR-7)."""
        if qty <= 0:
            raise ValidationFailed("Quantity must be positive")
        if self.lifecycle_state not in (AssetState.AVAILABLE, AssetState.RESERVED):
            raise ValidationFailed("Asset is not in a reservable state", code="INELIGIBLE")
        if qty > self.unreserved_quantity:
            message = _("Only %(n)s unit(s) free") % {"n": self.unreserved_quantity}
            raise InsufficientQuantity(message)
        previous = self.lifecycle_state
        self.reserved_quantity += qty
        fields = ["reserved_quantity"]
        if self.unreserved_quantity == 0 and self.lifecycle_state == AssetState.AVAILABLE:
            self.lifecycle_state = AssetState.RESERVED  # every free unit is now committed
            fields.append("lifecycle_state")
        self._save(*fields)
        self._emit(previous, by, "ALLOCATION", f"{qty} unit(s) reserved")

    def release(self, qty: int, by: User) -> None:
        """Return reserved units once (cancel before dispatch, UC-30)."""
        if qty <= 0 or qty > self.reserved_quantity:
            raise ValidationFailed("Cannot release more units than are reserved")
        previous = self.lifecycle_state
        self.reserved_quantity -= qty
        fields = ["reserved_quantity"]
        if self.lifecycle_state == AssetState.RESERVED:
            self.lifecycle_state = AssetState.AVAILABLE
            fields.append("lifecycle_state")
        self._save(*fields)
        self._emit(previous, by, "ALLOCATION", f"{qty} unit(s) released")

    def move_units(self, qty: int, to: Location, dept: Department, custodian: User, by: User) -> "Asset":
        """Receipt (UC-37): the only place custody, owner and location change (BR-9).

        Whole lot: this asset moves and becomes TRANSFERRED. Part of a lot: the units are split into a new
        Asset record for the receiving department, and this record keeps the rest.
        Returns the asset record that now holds the received units.
        """
        if qty <= 0 or qty > self.reserved_quantity:
            raise ValidationFailed("Can only move units that were reserved for this transfer")
        previous = self.lifecycle_state
        if qty == self.quantity:
            self.reserved_quantity -= qty
            self.owner_department, self.custodian = dept, custodian
            self.location_campus, self.location_building, self.location_room = to.campus, to.building, to.room
            self.lifecycle_state = AssetState.TRANSFERRED
            self.publication_status = PublicationStatus.UNPUBLISHED
            self._save("reserved_quantity", "owner_department", "custodian", "location_campus", "location_building",
                       "location_room", "lifecycle_state", "publication_status")
            self._emit(previous, by, "TRANSFER", f"{qty} unit(s) received by {dept}")
            return self

        # partial lot -> split
        self.quantity -= qty
        self.available_quantity -= qty
        self.reserved_quantity -= qty
        if self.lifecycle_state == AssetState.RESERVED and self.unreserved_quantity > 0:
            self.lifecycle_state = AssetState.AVAILABLE
        self._save("quantity", "available_quantity", "reserved_quantity", "lifecycle_state")
        self._emit(previous, by, "TRANSFER", f"{qty} unit(s) split off to {dept}")
        new = Asset.objects.create(
            name=self.name, description=self.description, specifications=self.specifications, category=self.category,
            owner_department=dept, custodian=custodian, quantity=qty, available_quantity=qty, reserved_quantity=0,
            location_campus=to.campus, location_building=to.building, location_room=to.room, condition=self.condition,
            purchase_date=self.purchase_date,
            estimated_value=self.estimated_value,  # per unit, so it is copied unchanged
            lifecycle_state=AssetState.TRANSFERRED, serial_number="", external_ref="",
        )
        new._emit(AssetState.REGISTERED, by, "TRANSFER", f"Created from {self.pk} by transfer of {qty} unit(s)")
        return new


def attachment_path(instance, filename):
    return f"assets/{instance.asset_id}/{instance.attachment_no}-{filename}"


class AssetAttachment(UUIDModel):
    """Weak entity (assetId, attachmentNo). Django needs a single primary key, so the partial key is a
    unique constraint instead."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="attachments")
    attachment_no = models.PositiveIntegerField()
    file = models.FileField(upload_to=attachment_path)
    file_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["asset", "attachment_no"], name="uniq_asset_attachment_no")]

    def download_url(self) -> str:
        return self.file.url


class TagSource(models.TextChoices):
    MANUAL = "MANUAL", _("Manual")
    AI_ACCEPTED = "AI_ACCEPTED", _("AI suggestion, accepted")


class AssetTag(UUIDModel):
    """Weak entity (assetId, tagText)."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="tags")
    tag_text = models.CharField(max_length=60)
    source = models.CharField(max_length=12, choices=TagSource.choices, default=TagSource.MANUAL)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["asset", "tag_text"], name="uniq_asset_tag")]

    def matches(self, term: str) -> bool:
        return term.strip().lower() in self.tag_text.lower()


# ----------------------------------------------------------------------------- Phase 7: questions on an asset

class AssetQuestion(UUIDModel):
    """A short question about one asset and the custodian's answer. Not a chat: one answer per question.
    Everyone who may view the asset sees the question and answer; only the asker, the custodian and the unit's
    asset managers see who asked (others see the asker's unit)."""

    QUESTION_MAX, ANSWER_MAX = 500, 1000

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="questions")
    asked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="asset_questions")
    asker_unit = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL, related_name="+")
    text = models.CharField(max_length=QUESTION_MAX)
    answer = models.CharField(max_length=ANSWER_MAX, blank=True)
    answered_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    asked_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-asked_at"]
        indexes = [models.Index(fields=["asset", "answered_at"])]

    @property
    def is_answered(self) -> bool:
        return self.answered_at is not None

    @property
    def is_closed(self) -> bool:
        """Unanswered, and the asset has left the register: kept for the record, no answer expected."""
        return not self.is_answered and self.asset.lifecycle_state in END_OF_LIFE_STATES

    def waiting_days(self) -> int:
        return (timezone.now() - self.asked_at).days


# ----------------------------------------------------------------------------- Phase 8: bulk CSV import

class ImportStatus(models.TextChoices):
    PREVIEW = "PREVIEW", _("Waiting for confirmation")
    IMPORTED = "IMPORTED", _("Imported")
    DISCARDED = "DISCARDED", _("Discarded")


class ImportBatch(UUIDModel):
    """One uploaded CSV: checked rows kept for the preview, then imported once. The file itself is not stored."""

    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    file_name = models.CharField(max_length=200)
    file_sha256 = models.CharField(max_length=64, db_index=True)
    rows = models.JSONField(default=list)        # [{"n": 2, "values": {...}, "errors": [...], "warnings": [...]}]
    status = models.CharField(max_length=10, choices=ImportStatus.choices, default=ImportStatus.PREVIEW)
    result = models.JSONField(default=dict)      # {"imported": [{"n", "asset"}], "failed": [{"n", "error"}], "published": n}
    created_at = models.DateTimeField(auto_now_add=True)
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def valid_rows(self) -> list:
        return [r for r in self.rows if not r["errors"]]

    @property
    def error_rows(self) -> list:
        return [r for r in self.rows if r["errors"]]

    @property
    def warning_rows(self) -> list:
        return [r for r in self.rows if r["warnings"] and not r["errors"]]
