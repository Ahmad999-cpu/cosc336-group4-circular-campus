"""Public interface of the Institution Blueprint module (bonus feature). OWNER: blueprint.

The admin describes the institution once (units, member types, approval routes); every other module reads
those tables. Every change here is audited. The AI may draft a setup, but only a person publishes it (D5).
"""
from __future__ import annotations

import copy
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _t

from apps.access.models import PERMISSIONS, Department, Permission, Role, RoleAssignment
from apps.access.permissions import require, users_who_can
from apps.ai.gateway import AIGateway
from apps.audit.services import record
from apps.catalogue.models import Asset, Category
from apps.common.enums import RecordStatus
from apps.common.errors import ValidationFailed

from .models import ApprovalRule, ApproverScope, BlueprintDraft, DraftStatus
from .routing import approval_route

PERMISSION_GROUPS = [
    ("Assets", ["asset.register", "asset.publish", "asset.custody"]),
    ("Requests", ["request.submit", "request.approve"]),
    ("Transfers", ["transfer.dispatch", "transfer.receive"]),
    ("Care", ["maintenance.record", "eol.propose", "eol.approve"]),
    ("Impact", ["sustainability.review", "reports.view", "reports.publish"]),
    ("Admin", ["admin.users", "admin.blueprint", "admin.ai"]),
]


def _ensure_permissions() -> None:
    for code, desc in PERMISSIONS.items():
        Permission.objects.get_or_create(code=code, defaults={"description": desc})


def _money(v, field: str) -> Decimal | None:
    if v in (None, ""):
        return None
    try:
        d = Decimal(str(v).replace(",", ""))
    except InvalidOperation:
        message = _t("%(field)s: enter a number in AED") % {"field": field}
        raise ValidationFailed(message)
    if d < 0:
        message = _t("%(field)s can't be negative") % {"field": field}
        raise ValidationFailed(message)
    return d


# ----------------------------------------------------------------------------- units

def unit_tree() -> list[tuple[Department, int]]:
    """Depth-first (unit, depth) list for the tree view, roots first, children by name."""
    units = list(Department.objects.order_by("name"))
    kids: dict = {}
    for u in units:
        kids.setdefault(u.parent_id, []).append(u)
    out = []

    def walk(parent_id, depth):
        for u in kids.get(parent_id, []):
            out.append((u, depth))
            walk(u.pk, depth + 1)

    walk(None, 0)
    return out


@transaction.atomic
def save_unit(by, data: dict, unit_id=None) -> Department:
    require(by, "admin.blueprint")
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationFailed("Give the unit a name")
    parent = data.get("parent") or None
    if isinstance(parent, str):
        parent = Department.objects.filter(pk=parent).first() if parent else None
    u = Department.objects.select_for_update().get(pk=unit_id) if unit_id else Department()
    if unit_id and parent is not None and (parent.pk == u.pk or u in parent.ancestors()):
        raise ValidationFailed("A unit can't sit inside itself or one of its own sub-units")
    before = {"name": u.name, "parent": str(u.parent_id or ""), "type": u.unit_type} if unit_id else None
    u.name, u.parent, u.unit_type = name[:200], parent, (data.get("unit_type") or "").strip()[:50]
    u.campus, u.building = (data.get("campus") or "").strip()[:100], (data.get("building") or "").strip()[:100]
    u.save()
    record(by, "blueprint_unit_update" if unit_id else "blueprint_unit_create", "Department", u.pk, before=before,
           after={"name": u.name, "parent": str(u.parent_id or ""), "type": u.unit_type})
    return u


@transaction.atomic
def set_unit_status(by, unit_id, active: bool) -> Department:
    require(by, "admin.blueprint")
    u = Department.objects.select_for_update().get(pk=unit_id)
    if not active:
        if u.children.filter(status=RecordStatus.ACTIVE).exists():
            raise ValidationFailed("Deactivate or move its sub-units first")
        if Asset.objects.filter(owner_department=u, quantity__gt=0).exclude(lifecycle_state__in=["RETIRED", "DONATED", "RECYCLED", "DISPOSED"]).exists():
            raise ValidationFailed("This unit still owns assets. Transfer or retire them first")
        u.deactivate()
    else:
        u.status = RecordStatus.ACTIVE
        u.save(update_fields=["status"])
    record(by, "blueprint_unit_status", "Department", u.pk, after={"status": u.status})
    return u


# ----------------------------------------------------------------------------- member types

@transaction.atomic
def save_role(by, data: dict, role_id=None) -> Role:
    require(by, "admin.blueprint")
    _ensure_permissions()
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationFailed("Give the member type a name")
    codes = [c for c in data.get("permissions", []) if c]
    unknown = sorted(set(codes) - set(PERMISSIONS))
    if unknown:
        message = _t("Unknown permission: %(codes)s") % {"codes": ", ".join(unknown)}
        raise ValidationFailed(message)
    if Role.objects.filter(name__iexact=name).exclude(pk=role_id).exists():
        raise ValidationFailed("A member type with that name already exists")
    r = Role.objects.select_for_update().get(pk=role_id) if role_id else Role()
    before = {"name": r.name, "limit": str(r.approval_limit), "perms": sorted(r.permissions.values_list("code", flat=True))} if role_id else None
    if role_id and "admin.blueprint" not in codes and r.permits("admin.blueprint") and \
            not Role.objects.exclude(pk=r.pk).filter(permissions__code="admin.blueprint", assignments__active=True).exists():
        raise ValidationFailed("At least one member type with people in it must keep 'Edit the Institution Blueprint'")
    r.name, r.name_ar = name[:80], (data.get("name_ar") or "").strip()[:80]
    r.description = (data.get("description") or "").strip()[:300]
    r.approval_limit = _money(data.get("approval_limit"), _t("Approval limit"))
    r.save()
    r.permissions.set(Permission.objects.filter(code__in=codes))
    record(by, "blueprint_role_update" if role_id else "blueprint_role_create", "Role", r.pk, before=before,
           after={"name": r.name, "limit": str(r.approval_limit), "perms": sorted(codes)})
    return r


def role_matrix():
    roles = list(Role.objects.prefetch_related("permissions").order_by("name"))
    counts = {}
    for ra in RoleAssignment.objects.filter(active=True).values_list("role_id", flat=True):
        counts[ra] = counts.get(ra, 0) + 1
    for r in roles:
        r.codes = {p.code for p in r.permissions.all()}
        r.people = counts.get(r.pk, 0)
    return roles


# ----------------------------------------------------------------------------- approval routes

@transaction.atomic
def save_rule(by, data: dict, rule_id=None) -> ApprovalRule:
    require(by, "admin.blueprint")
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationFailed("Give the route a name")
    role = data.get("approver_role")
    role = role if isinstance(role, Role) else Role.objects.filter(pk=role).first() if role else None
    if role is None:
        raise ValidationFailed("Pick who approves")
    if not role.permits("request.approve"):
        message = _t("%(role)s can't approve requests. Tick 'Approve or reject' for that member type first") % {"role": role.display_name}
        raise ValidationFailed(message)
    lo, hi = _money(data.get("min_value"), _t("From")), _money(data.get("max_value"), _t("Up to"))
    if lo is not None and hi is not None and lo > hi:
        raise ValidationFailed("'From' is more than 'Up to'")
    cat = data.get("category")
    cat = cat if isinstance(cat, Category) else Category.objects.filter(pk=cat).first() if cat else None
    scope = data.get("approver_scope") or ApproverScope.OWNING_UNIT
    if scope not in ApproverScope.values:
        raise ValidationFailed("Unknown approver scope")
    try:
        priority = int(data.get("priority") or 100)
    except ValueError:
        raise ValidationFailed("Priority must be a whole number")
    rule = ApprovalRule.objects.select_for_update().get(pk=rule_id) if rule_id else ApprovalRule()
    rule.name, rule.priority, rule.category, rule.min_value, rule.max_value = name[:120], max(1, priority), cat, lo, hi
    rule.approver_role, rule.approver_scope = role, scope
    rule.active = bool(data.get("active", True))
    rule.save()
    record(by, "blueprint_rule_update" if rule_id else "blueprint_rule_create", "ApprovalRule", rule.pk,
           after={"name": rule.name, "priority": rule.priority, "role": role.name, "scope": scope,
                  "category": cat.name if cat else "", "min": str(lo), "max": str(hi), "active": rule.active})
    return rule


@transaction.atomic
def toggle_rule(by, rule_id) -> ApprovalRule:
    require(by, "admin.blueprint")
    r = ApprovalRule.objects.select_for_update().get(pk=rule_id)
    r.active = not r.active
    r.save(update_fields=["active"])
    record(by, "blueprint_rule_toggle", "ApprovalRule", r.pk, after={"active": r.active})
    return r


def describe_rule(rule: ApprovalRule) -> str:
    parts = [rule.category.display_name if rule.category_id else "Any category"]
    if rule.min_value is not None and rule.max_value is not None:
        parts.append(f"AED {rule.min_value:,.0f} to {rule.max_value:,.0f}")
    elif rule.min_value is not None:
        parts.append(f"from AED {rule.min_value:,.0f}")
    elif rule.max_value is not None:
        parts.append(f"up to AED {rule.max_value:,.0f}")
    return ", ".join(parts)


def who_approves(asset: Asset, quantity: int) -> dict:
    """The route a request for this item would take, and the people who could approve it today."""
    quantity = max(1, int(quantity))
    value = asset.estimated_value * quantity if asset.estimated_value is not None else None
    route = approval_route(asset, quantity)
    rule = None
    if route is not None:
        rule = next((r for r in ApprovalRule.objects.filter(active=True).select_related("category")
                     if r.matches(asset.category, value)), None)
        role, unit = route
        people = [u for u in users_who_can("request.approve", unit or asset.owner_department)
                  if u.role_assignments.filter(role=role, active=True).exists()]
    else:
        role, unit = None, asset.owner_department
        people = list(users_who_can("request.approve", asset.owner_department))
    if value is not None:
        people = [u for u in people if any(ra.role.approval_limit is None or ra.role.approval_limit >= value
                                           for ra in u.role_assignments.filter(active=True, role__permissions__code="request.approve").select_related("role"))]
    return {"asset": asset, "quantity": quantity, "value": value, "rule": rule, "role": role, "unit": unit, "people": people}


# ----------------------------------------------------------------------------- drafts: templates and AI

TEMPLATES = {
    "university": {
        "label": "University",
        "units": [{"name": "University", "unit_type": "University", "parent": None},
                  {"name": "College of Engineering", "unit_type": "College", "parent": "University"},
                  {"name": "College of Science", "unit_type": "College", "parent": "University"},
                  {"name": "Library", "unit_type": "Service", "parent": "University"},
                  {"name": "Facilities", "unit_type": "Service", "parent": "University"},
                  {"name": "Student Clubs", "unit_type": "Student life", "parent": "University"}],
        "roles": [{"name": "Requester", "permissions": ["request.submit", "transfer.receive"], "approval_limit": None},
                  {"name": "Asset Custodian", "permissions": ["asset.register", "asset.publish", "asset.custody", "maintenance.record", "eol.propose", "transfer.receive"], "approval_limit": None},
                  {"name": "Head of Department", "permissions": ["request.approve", "eol.approve", "reports.view"], "approval_limit": 5000},
                  {"name": "Dean", "permissions": ["request.approve", "eol.approve", "reports.view"], "approval_limit": None},
                  {"name": "Facilities Coordinator", "permissions": ["transfer.dispatch"], "approval_limit": None},
                  {"name": "Sustainability Officer", "permissions": ["sustainability.review", "reports.view", "reports.publish"], "approval_limit": None}],
        "rules": [{"name": "High-value items go to the Dean", "priority": 10, "category": None, "min_value": 5000, "max_value": None,
                   "approver_role": "Dean", "approver_scope": "PARENT_UNIT"},
                  {"name": "Everything else: Head of Department", "priority": 100, "category": None, "min_value": None, "max_value": None,
                   "approver_role": "Head of Department", "approver_scope": "OWNING_UNIT"}],
    },
    "school": {
        "label": "School",
        "units": [{"name": "School", "unit_type": "School", "parent": None},
                  {"name": "Primary", "unit_type": "Section", "parent": "School"},
                  {"name": "Secondary", "unit_type": "Section", "parent": "School"},
                  {"name": "Science labs", "unit_type": "Department", "parent": "Secondary"},
                  {"name": "Operations", "unit_type": "Service", "parent": "School"}],
        "roles": [{"name": "Teacher", "permissions": ["request.submit", "transfer.receive", "maintenance.record"], "approval_limit": None},
                  {"name": "Lab Technician", "permissions": ["asset.register", "asset.publish", "asset.custody", "maintenance.record", "eol.propose"], "approval_limit": None},
                  {"name": "Section Head", "permissions": ["request.approve", "eol.approve", "reports.view"], "approval_limit": 2000},
                  {"name": "Principal", "permissions": ["request.approve", "eol.approve", "reports.view", "reports.publish"], "approval_limit": None},
                  {"name": "Operations Officer", "permissions": ["transfer.dispatch"], "approval_limit": None}],
        "rules": [{"name": "Over AED 2,000 goes to the Principal", "priority": 10, "category": None, "min_value": 2000, "max_value": None,
                   "approver_role": "Principal", "approver_scope": "INSTITUTION"},
                  {"name": "Section heads approve the rest", "priority": 100, "category": None, "min_value": None, "max_value": None,
                   "approver_role": "Section Head", "approver_scope": "PARENT_UNIT"}],
    },
    "hospital": {
        "label": "Hospital",
        "units": [{"name": "Hospital", "unit_type": "Hospital", "parent": None},
                  {"name": "Clinical services", "unit_type": "Division", "parent": "Hospital"},
                  {"name": "Outpatients", "unit_type": "Ward", "parent": "Clinical services"},
                  {"name": "Radiology", "unit_type": "Department", "parent": "Clinical services"},
                  {"name": "Biomedical engineering", "unit_type": "Department", "parent": "Hospital"},
                  {"name": "Administration", "unit_type": "Division", "parent": "Hospital"}],
        "roles": [{"name": "Staff Member", "permissions": ["request.submit", "transfer.receive"], "approval_limit": None},
                  {"name": "Equipment Custodian", "permissions": ["asset.register", "asset.publish", "asset.custody", "eol.propose"], "approval_limit": None},
                  {"name": "Biomedical Engineer", "permissions": ["maintenance.record", "asset.custody"], "approval_limit": None},
                  {"name": "Department Manager", "permissions": ["request.approve", "eol.approve", "reports.view"], "approval_limit": 10000},
                  {"name": "Supply Chain", "permissions": ["transfer.dispatch", "request.approve", "reports.view"], "approval_limit": None}],
        "rules": [{"name": "Medical equipment over AED 10,000: Supply Chain", "priority": 10, "category": None, "min_value": 10000, "max_value": None,
                   "approver_role": "Supply Chain", "approver_scope": "INSTITUTION"},
                  {"name": "Department managers approve the rest", "priority": 100, "category": None, "min_value": None, "max_value": None,
                   "approver_role": "Department Manager", "approver_scope": "OWNING_UNIT"}],
    },
}


def _clean_template(key: str) -> dict:
    t = copy.deepcopy(TEMPLATES[key])
    t.pop("label", None)
    return t


@transaction.atomic
def draft_from_template(by, key: str) -> BlueprintDraft:
    require(by, "admin.blueprint")
    if key not in TEMPLATES:
        raise ValidationFailed("Unknown template")
    d = BlueprintDraft.objects.create(description=f"Template: {TEMPLATES[key]['label']}", draft=_clean_template(key), created_by=by)
    record(by, "blueprint_draft", "BlueprintDraft", d.pk, after={"source": f"template:{key}"})
    return d


def draft_from_description(by, description: str, gateway: AIGateway | None = None) -> tuple[BlueprintDraft | None, str]:
    """AI drafts units, member types and routes from plain words. Returns (draft, message). Nothing is written
    to the real tables until a person publishes (D5)."""
    require(by, "admin.blueprint")
    text = (description or "").strip()
    if len(text) < 20:
        raise ValidationFailed("Describe the institution in a sentence or two (units, who approves what)")
    result = (gateway or AIGateway()).draft_blueprint({"description": text[:3000], "permissions": PERMISSIONS,
                                                       "scopes": list(ApproverScope.values)}, by)
    if not result.ok or not isinstance(result.value, dict):
        return None, "The AI couldn't draft a setup right now. Start from a template instead; you can edit everything."
    draft = normalise_draft(result.value)
    d = BlueprintDraft.objects.create(description=text, draft=draft, created_by=by, inference_id=result.inference_id)
    record(by, "blueprint_draft", "BlueprintDraft", d.pk, after={"source": "ai", "inference": str(result.inference_id)})
    return d, ""


def normalise_draft(raw: dict) -> dict:
    """Keep only the fields we understand, with safe types. Anything odd becomes a validation message later."""
    def s(v, n=120):
        return str(v).strip()[:n] if v not in (None, "") else None

    def num(v):
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    out = {"units": [], "roles": [], "rules": []}
    for u in raw.get("units") or []:
        if isinstance(u, dict) and s(u.get("name")):
            out["units"].append({"name": s(u["name"], 200), "unit_type": s(u.get("unit_type"), 50) or "", "parent": s(u.get("parent"), 200)})
    for r in raw.get("roles") or []:
        if isinstance(r, dict) and s(r.get("name")):
            perms = [p for p in (r.get("permissions") or []) if isinstance(p, str)]
            out["roles"].append({"name": s(r["name"], 80), "permissions": perms, "approval_limit": num(r.get("approval_limit"))})
    for x in raw.get("rules") or []:
        if isinstance(x, dict) and s(x.get("name")):
            out["rules"].append({"name": s(x["name"]), "priority": int(num(x.get("priority")) or 100), "category": s(x.get("category")),
                                 "min_value": num(x.get("min_value")), "max_value": num(x.get("max_value")),
                                 "approver_role": s(x.get("approver_role"), 80), "approver_scope": s(x.get("approver_scope"), 12) or "OWNING_UNIT"})
    return out


def review(draft: BlueprintDraft) -> dict:
    """What publishing would do, item by item: new / already exists / problem."""
    d = draft.draft or {}
    have_units = {u.lower() for u in Department.objects.values_list("name", flat=True)}
    have_roles = {r.lower() for r in Role.objects.values_list("name", flat=True)}
    have_cats = {c.lower() for c in Category.objects.values_list("name", flat=True)}
    draft_units = {u["name"].lower() for u in d.get("units", [])}
    draft_roles = {r["name"].lower(): r for r in d.get("roles", [])}
    units, roles, rules = [], [], []
    for i, u in enumerate(d.get("units", [])):
        problem = ""
        if u.get("parent") and u["parent"].lower() not in draft_units | have_units:
            problem = f"Parent '{u['parent']}' is not in the draft or the current setup"
        units.append({"i": i, **u, "exists": u["name"].lower() in have_units, "problem": problem})
    for i, r in enumerate(d.get("roles", [])):
        unknown = sorted(set(r.get("permissions", [])) - set(PERMISSIONS))
        roles.append({"i": i, **r, "labels": [PERMISSIONS.get(p, p) for p in r.get("permissions", []) if p in PERMISSIONS],
                      "exists": r["name"].lower() in have_roles,
                      "problem": f"Unknown permission: {', '.join(unknown)}" if unknown else ""})
    for i, x in enumerate(d.get("rules", [])):
        problem = ""
        role_name = (x.get("approver_role") or "").lower()
        draft_role = draft_roles.get(role_name)
        if not role_name or (role_name not in have_roles and draft_role is None):
            problem = f"Approver '{x.get('approver_role')}' is not a member type"
        elif draft_role is not None and "request.approve" not in draft_role.get("permissions", []):
            problem = f"{x.get('approver_role')} can't approve requests in this draft"
        elif x.get("category") and x["category"].lower() not in have_cats:
            problem = f"Category '{x['category']}' doesn't exist"
        elif x.get("approver_scope") not in ApproverScope.values:
            problem = "Unknown approver scope"
        rules.append({"i": i, **x, "problem": problem})
    return {"units": units, "roles": roles, "rules": rules,
            "problems": sum(1 for x in units + roles + rules if x["problem"])}


@transaction.atomic
def publish_draft(draft_id, by, include: dict | None = None) -> dict:
    """Write the ticked items in one transaction. Additive: existing units and member types with the same name
    are kept as they are (their settings are not overwritten). Any problem in a ticked item stops everything."""
    require(by, "admin.blueprint")
    _ensure_permissions()
    draft = BlueprintDraft.objects.select_for_update().get(pk=draft_id)
    if draft.status != DraftStatus.DRAFT:
        raise ValidationFailed("This draft was already published or discarded")
    rv = review(draft)
    pick = include or {k: {x["i"] for x in rv[k]} for k in ("units", "roles", "rules")}
    chosen = {k: [x for x in rv[k] if x["i"] in pick.get(k, set())] for k in ("units", "roles", "rules")}
    bad = [x["problem"] for k in chosen for x in chosen[k] if x["problem"]]
    if bad:
        raise ValidationFailed("Fix these first: " + "; ".join(bad[:3]))
    made = {"units": 0, "roles": 0, "rules": 0}

    by_name = {d.name.lower(): d for d in Department.objects.all()}
    pending = [u for u in chosen["units"] if not u["exists"]]
    for _ in range(len(pending) + 1):  # parents first, whatever order the draft lists them in
        for u in list(pending):
            parent = by_name.get((u.get("parent") or "").lower()) if u.get("parent") else None
            if u.get("parent") and parent is None:
                continue
            dep = Department.objects.create(name=u["name"], unit_type=u.get("unit_type") or "", parent=parent)
            by_name[dep.name.lower()] = dep
            pending.remove(u)
            made["units"] += 1
    if pending:
        raise ValidationFailed("Some units' parents weren't ticked: " + ", ".join(u["name"] for u in pending))

    roles = {r.name.lower(): r for r in Role.objects.all()}
    for r in chosen["roles"]:
        if r["exists"]:
            continue
        role = Role.objects.create(name=r["name"], approval_limit=Decimal(str(r["approval_limit"])) if r.get("approval_limit") is not None else None)
        role.permissions.set(Permission.objects.filter(code__in=r.get("permissions", [])))
        roles[role.name.lower()] = role
        made["roles"] += 1

    cats = {c.name.lower(): c for c in Category.objects.all()}
    for x in chosen["rules"]:
        role = roles.get((x.get("approver_role") or "").lower())
        if role is None:
            message = _t("Tick the member type '%(role)s' too: the route '%(route)s' needs it") % {"role": x.get("approver_role"), "route": x["name"]}
            raise ValidationFailed(message)
        ApprovalRule.objects.create(name=x["name"], priority=x.get("priority") or 100,
                                    category=cats.get((x.get("category") or "").lower()) if x.get("category") else None,
                                    min_value=Decimal(str(x["min_value"])) if x.get("min_value") is not None else None,
                                    max_value=Decimal(str(x["max_value"])) if x.get("max_value") is not None else None,
                                    approver_role=role, approver_scope=x.get("approver_scope") or ApproverScope.OWNING_UNIT)
        made["rules"] += 1

    draft.status, draft.published_by, draft.published_at = DraftStatus.PUBLISHED, by, timezone.now()
    draft.save(update_fields=["status", "published_by", "published_at"])
    record(by, "blueprint_publish", "BlueprintDraft", draft.pk, after=made)
    return made


@transaction.atomic
def discard_draft(draft_id, by) -> None:
    require(by, "admin.blueprint")
    d = BlueprintDraft.objects.select_for_update().get(pk=draft_id)
    if d.status == DraftStatus.DRAFT:
        d.status = DraftStatus.DISCARDED
        d.save(update_fields=["status"])
        record(by, "blueprint_discard", "BlueprintDraft", d.pk)
