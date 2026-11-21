"""Institution Blueprint setup screens (bonus feature). Everything here needs admin.blueprint."""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.access.models import PERMISSIONS, Department, Role, User
from apps.catalogue.models import Asset, Category
from apps.catalogue.services import published
from apps.web.htmx import redirect_htmx, with_toast

from . import services
from .models import ApprovalRule, ApproverScope, BlueprintDraft, DraftStatus

TABS = [("units", _("Units")), ("roles", _("Member types")), ("routes", _("Approval routes")), ("start", _("Quick start"))]


def _back(request, tab, text):
    messages.success(request, text)
    return redirect_htmx(reverse("blueprint:index") + f"?tab={tab}")


@needs("admin.blueprint")
def index(request):
    tab = request.GET.get("tab") if request.GET.get("tab") in dict(TABS) else "units"
    ctx = {"tabs": TABS, "tab": tab}
    if tab == "units":
        tree = services.unit_tree()
        counts = {}
        for dept_id in Asset.objects.exclude(quantity=0).values_list("owner_department_id", flat=True):
            counts[dept_id] = counts.get(dept_id, 0) + 1
        people = {}
        for dept_id in User.objects.filter(account_status="ACTIVE").values_list("department_id", flat=True):
            people[dept_id] = people.get(dept_id, 0) + 1
        ctx["tree"] = [(u, depth, counts.get(u.pk, 0), people.get(u.pk, 0)) for u, depth in tree]
    elif tab == "roles":
        ctx["roles"] = services.role_matrix()
        ctx["groups"] = [(g, [(c, PERMISSIONS[c]) for c in codes]) for g, codes in services.PERMISSION_GROUPS]
    elif tab == "routes":
        rules = list(ApprovalRule.objects.select_related("category", "approver_role").order_by("priority", "name"))
        for r in rules:
            r.summary = services.describe_rule(r)
        ctx["rules"] = rules
        ctx["assets"] = published().select_related("owner_department").order_by("name")[:200]
    else:
        ctx["templates"] = [(k, v["label"], len(v["units"]), len(v["roles"]), len(v["rules"])) for k, v in services.TEMPLATES.items()]
        ctx["drafts"] = BlueprintDraft.objects.filter(status=DraftStatus.DRAFT).order_by("-created_at")[:5]
    return render(request, "blueprint/index.html", ctx)


# ----------------------------------------------------------------------------- units

@needs("admin.blueprint")
def unit_form(request, pk=None):
    unit = get_object_or_404(Department, pk=pk) if pk else None
    if request.method == "POST":
        services.save_unit(request.user, request.POST, unit_id=pk)
        return _back(request, "units", _("Unit saved."))
    parents = Department.objects.filter(status="ACTIVE").exclude(pk=pk).order_by("name") if pk else Department.objects.filter(status="ACTIVE").order_by("name")
    return render(request, "blueprint/_unit_form.html", {"unit": unit, "parents": parents,
                                                         "parent_id": request.GET.get("parent", "")})


@needs("admin.blueprint")
@require_POST
def unit_status(request, pk):
    active = request.POST.get("active") == "1"
    services.set_unit_status(request.user, pk, active)
    return _back(request, "units", _("Unit reactivated.") if active else _("Unit deactivated."))


# ----------------------------------------------------------------------------- member types

@needs("admin.blueprint")
def role_form(request, pk=None):
    role = get_object_or_404(Role, pk=pk) if pk else None
    if request.method == "POST":
        data = {**request.POST.dict(), "permissions": request.POST.getlist("permissions")}
        services.save_role(request.user, data, role_id=pk)
        return _back(request, "roles", _("Member type saved."))
    have = set(role.permissions.values_list("code", flat=True)) if role else set()
    groups = [(g, [(c, PERMISSIONS[c], c in have) for c in codes]) for g, codes in services.PERMISSION_GROUPS]
    return render(request, "blueprint/_role_form.html", {"role": role, "groups": groups})


# ----------------------------------------------------------------------------- approval routes

@needs("admin.blueprint")
def rule_form(request, pk=None):
    rule = get_object_or_404(ApprovalRule, pk=pk) if pk else None
    if request.method == "POST":
        data = request.POST.dict()
        data["active"] = request.POST.get("active") == "on"
        services.save_rule(request.user, data, rule_id=pk)
        return _back(request, "routes", _("Approval route saved."))
    return render(request, "blueprint/_rule_form.html", {
        "rule": rule, "roles": Role.objects.filter(permissions__code="request.approve").order_by("name"),
        "categories": Category.objects.order_by("name"), "scopes": ApproverScope.choices})


@needs("admin.blueprint")
@require_POST
def rule_toggle(request, pk):
    r = services.toggle_rule(request.user, pk)
    return _back(request, "routes", _("Route turned on.") if r.active else _("Route turned off."))


@needs("admin.blueprint")
def try_route(request):
    asset = Asset.objects.filter(pk=request.GET.get("asset")).select_related("category", "owner_department").first() if request.GET.get("asset") else None
    result = None
    if asset is not None:
        try:
            qty = max(1, int(request.GET.get("qty") or 1))
        except ValueError:
            qty = 1
        result = services.who_approves(asset, qty)
        if result["rule"] is not None:
            result["rule"].summary = services.describe_rule(result["rule"])
    return render(request, "blueprint/_try.html", {"r": result})


# ----------------------------------------------------------------------------- drafts

@needs("admin.blueprint")
@require_POST
def from_template(request, key):
    d = services.draft_from_template(request.user, key)
    return redirect_htmx(reverse("blueprint:draft", args=[d.pk]))


@needs("admin.blueprint")
@require_POST
def from_description(request):
    d, msg = services.draft_from_description(request.user, request.POST.get("description", ""))
    if d is None:
        return with_toast(HttpResponse(status=204), msg, ok=False)
    return redirect_htmx(reverse("blueprint:draft", args=[d.pk]))


@needs("admin.blueprint")
def draft(request, pk):
    d = get_object_or_404(BlueprintDraft, pk=pk)
    return render(request, "blueprint/draft.html", {"d": d, "rv": services.review(d), "is_open": d.status == DraftStatus.DRAFT})


@needs("admin.blueprint")
@require_POST
def publish(request, pk):
    include = {k: {int(i) for i in request.POST.getlist(k) if i.isdigit()} for k in ("units", "roles", "rules")}
    made = services.publish_draft(pk, request.user, include)
    messages.success(request, _("Published: %(u)s units, %(r)s member types, %(x)s approval routes added.") %
                     {"u": made["units"], "r": made["roles"], "x": made["rules"]})
    return redirect_htmx(reverse("blueprint:index") + "?tab=units") if request.headers.get("HX-Request") else redirect(reverse("blueprint:index"))


@needs("admin.blueprint")
@require_POST
def discard(request, pk):
    services.discard_draft(pk, request.user)
    return _back(request, "start", _("Draft discarded."))
