"""Screens of the Assets & Catalogue module: Browse (marketplace), asset panel, Our assets console, register/edit."""
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.access.permissions import can, has_any
from apps.common.errors import ValidationFailed
from apps.web.htmx import is_htmx, with_toast

from . import services
from .forms import AssetForm, BrowseFilter, MineFilter
from .models import Asset, AssetState, PublicationStatus


@login_required
def browse(request):
    """C3: everything published for reuse, with keyword search and filters."""
    f = BrowseFilter(request.GET or None, campuses=services.campuses())
    data = f.cleaned_data if f.is_valid() else {}
    assets = services.search(q=data.get("q", ""), category=data.get("category"), condition=data.get("condition", ""),
                             campus=data.get("campus", ""), max_age_years=data.get("max_age_years") or None,
                             sort=data.get("sort") or "units")
    soon = services.search(services.upcoming(), q=data.get("q", ""), category=data.get("category"), condition=data.get("condition", ""),
                           campus=data.get("campus", ""), sort="name")
    ctx = {"filter": f, "assets": assets[:120], "count": assets.count(), "categories": services.top_categories(),
           "active_category": data.get("category"), "soon": soon[:48]}
    if is_htmx(request) and request.GET.get("partial"):
        return render(request, "catalogue/_grid.html", ctx)
    return render(request, "catalogue/browse.html", ctx)


def _visible(user, asset) -> bool:
    return services.can_view(user, asset)


def _can_advise(user, asset) -> bool:
    """Feature 2 button. The rule lives in Sustainability (a higher module), so it is repeated here as plain
    permission codes; the advice view checks the real rule again on the server."""
    return asset.custodian_id == user.pk or any(
        can(user, a, asset.owner_department) for a in ("asset.register", "asset.custody", "maintenance.record",
                                                       "eol.propose", "eol.approve", "sustainability.review"))


def _panel_ctx(request, asset):
    return {
        "asset": asset,
        "history": asset.history.select_related("recorded_by").order_by("-recorded_at")[:10],
        "free": asset.unreserved_quantity,
        "can_request": has_any(request.user, "request.submit") and asset.publication_status == PublicationStatus.PUBLISHED and asset.unreserved_quantity > 0,
        "can_manage": can(request.user, "asset.register", asset.owner_department),
        "can_maintain": can(request.user, "maintenance.record", asset.owner_department),
        "can_eol": can(request.user, "eol.propose", asset.owner_department),
        "can_label": services.can_label(request.user, asset) and asset.lifecycle_state not in services.GONE_STATES,
        "gone": asset.lifecycle_state in services.GONE_STATES,
        "can_advise": _can_advise(request.user, asset),
        "can_schedule": can(request.user, "asset.publish", asset.owner_department) and asset.publication_status != PublicationStatus.PUBLISHED
                        and asset.lifecycle_state in Asset.UPCOMING_FROM,
        "can_interest": asset.is_upcoming and has_any(request.user, "request.submit") and request.user.department_id != asset.owner_department_id,
        "interested": asset.is_upcoming and asset.interests.filter(owner=request.user).exists(),
        **_qa_ctx(request, asset),
    }


@login_required
def panel(request, pk):
    """The asset page. Also what a QR label opens: same sign-in and visibility rules for both (Feature 1).
    A missing asset and one this person may not see get the same answer, so a label reveals nothing."""
    asset = Asset.objects.select_related("category", "owner_department", "custodian").filter(pk=pk).first()
    if asset is None or not _visible(request.user, asset):
        if is_htmx(request):
            raise Http404()
        return render(request, "catalogue/missing.html", status=404)
    template = "catalogue/_panel.html" if is_htmx(request) else "catalogue/detail.html"
    return render(request, template, _panel_ctx(request, asset))


def _label_asset(request, pk) -> Asset:
    asset = Asset.objects.select_related("category", "owner_department", "custodian").filter(pk=pk).first()
    if asset is None or not services.can_label(request.user, asset):
        raise Http404()
    return asset


@login_required
def qr_label(request, pk):
    """Feature 1: the printable label (code + name + short id), with print and download buttons."""
    from . import qr
    asset = _label_asset(request, pk)
    ctx = {"asset": asset, "gone": asset.lifecycle_state in services.GONE_STATES, "short_id": qr.short_id(asset),
           "base_set": qr.base_url_configured()}
    if not ctx["gone"]:
        url = qr.asset_url(asset, request)
        ctx.update(url=url, code=qr.code_svg(url, 220))
    return render(request, "catalogue/qr_label.html", ctx)


@login_required
def qr_download(request, pk):
    """Feature 1: the same label as an SVG file (prints sharp at any size; opens in browsers and Word)."""
    from django.http import HttpResponse

    from . import qr
    asset = _label_asset(request, pk)
    try:
        services.require_label(request.user, asset)
    except ValidationFailed:
        raise Http404()
    svg = qr.label_svg(asset, qr.asset_url(asset, request), scan_hint=_("Scan to open. Sign-in required."), id_label=_("Asset ID"))
    resp = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{qr.download_name(asset)}"'
    resp["X-Content-Type-Options"] = "nosniff"
    return resp


@needs("asset.register")
def mine(request):
    """C2: the custodian's console for the units they look after."""
    f = MineFilter(request.GET or None)
    data = f.cleaned_data if f.is_valid() else {}
    qs = services.search(services.managed_by(request.user), q=data.get("q", ""), state=data.get("state", ""), sort="newest")
    counts = {s: services.managed_by(request.user).filter(lifecycle_state=s).count() for s in (AssetState.REGISTERED, AssetState.AVAILABLE)}
    ctx = {"filter": f, "assets": qs[:300], "states": AssetState, "registered": counts[AssetState.REGISTERED],
           "available": counts[AssetState.AVAILABLE],
           "published": services.managed_by(request.user).filter(publication_status=PublicationStatus.PUBLISHED).count(),
           "questions_waiting": services.unanswered_count(request.user)}
    if is_htmx(request) and request.GET.get("partial"):
        return render(request, "catalogue/_mine_rows.html", ctx)
    return render(request, "catalogue/mine.html", ctx)


@needs("asset.register")
def new(request):
    form = AssetForm(request.POST or None, request.FILES or None, user=request.user,
                     initial={"quantity": 1, "condition": "GOOD", "location_campus": "Main"})
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        tags, photo = data.pop("tags"), data.pop("photo")
        # Tags the person added from the AI suggestion (and kept) are stored as "AI suggestion, accepted".
        from_ai = {t.strip().lower() for t in request.POST.get("ai_tags", "").split(",") if t.strip()}
        all_tags = services.clean_tags(tags)
        manual = [t for t in all_tags if t.lower() not in from_ai]
        accepted = [t for t in all_tags if t.lower() in from_ai]
        try:
            asset = services.register_asset(request.user, data, uploads=[photo], tags=",".join(manual), ai_tags=accepted)
        except ValidationFailed as e:
            form.add_error(None, str(e))
        else:
            _record_ai_use(request)
            resp = render(request, "catalogue/_mine_row.html", {"a": asset, "states": AssetState})
            resp["HX-Retarget"] = "#rows"
            resp["HX-Reswap"] = "afterbegin"
            return with_toast(resp, _("Registered %(name)s. Confirm its condition, then publish it.") % {"name": asset.name}, close_drawer=True)
    return render(request, "catalogue/_form.html", {"form": form, "campuses": services.campuses(), "new": True})


def _record_ai_use(request) -> None:
    """Section 9.7: what the person did with the AI suggestion (used some of it, or ignored it)."""
    from apps.ai.models import AIInferenceRecord
    from apps.common.enums import UserDecision
    rec = AIInferenceRecord.objects.filter(pk=request.POST.get("ai_inference") or None, user=request.user).first() \
        if len(request.POST.get("ai_inference", "")) == 36 else None
    if rec is not None and not rec.user_decision:
        used = sorted({u for u in request.POST.get("ai_used", "").split(",") if u})
        rec.record_decision(UserDecision.ACCEPTED if used else UserDecision.IGNORED, ", ".join(used)[:300])


@needs("asset.register")
@require_POST
def suggest(request):
    """AI 1 (optional): suggestions for the registration form. Nothing is filled in until the person clicks Use."""
    s = services.suggest_details(request.user, request.POST, request.FILES.get("photo"))
    return render(request, "catalogue/_suggest.html", {"s": s})


@needs("asset.register")
def edit(request, pk):
    asset = get_object_or_404(services.managed_by(request.user), pk=pk)
    tags = ", ".join(asset.tags.values_list("tag_text", flat=True))
    form = AssetForm(request.POST or None, request.FILES or None, instance=asset, user=request.user, editing=True,
                     initial={"tags": tags})
    if request.method == "POST":
        if form.is_valid():
            data = dict(form.cleaned_data)
            new_tags, photo = data.pop("tags"), data.pop("photo")
            try:
                services.update_asset(request.user, asset, data, uploads=[photo], tags=new_tags)
            except ValidationFailed as e:
                form.add_error(None, str(e))
            else:
                asset.refresh_from_db()
                resp = render(request, "catalogue/_mine_row.html", {"a": asset, "states": AssetState})
                resp["HX-Retarget"] = f"#row-{asset.pk}"
                resp["HX-Reswap"] = "outerHTML"
                return with_toast(resp, _("Saved %(name)s.") % {"name": asset.name}, close_drawer=True)
    return render(request, "catalogue/_form.html", {"form": form, "campuses": services.campuses(), "asset": asset})


@needs("asset.register")
@require_POST
def act(request, pk, action):
    """Publish, unpublish or confirm condition from the console row; answers with the updated row."""
    asset = get_object_or_404(services.managed_by(request.user), pk=pk)
    if action == "publish":
        asset, msg = services.publish(request.user, asset), _("%(name)s is now in the marketplace.")
    elif action == "unpublish":
        asset, msg = services.unpublish(request.user, asset), _("%(name)s is no longer in the marketplace.")
    elif action == "confirm":
        asset, msg = services.confirm_condition(request.user, asset, request.POST.get("condition") or asset.condition), _("%(name)s is available. Publish it when you're ready.")
    else:
        raise Http404()
    resp = render(request, "catalogue/_mine_row.html", {"a": asset, "states": AssetState, "flash": True})
    return with_toast(resp, msg % {"name": asset.name})


# ----------------------------------------------------------------------------- Phase 6: coming soon

@needs("asset.publish")
def upcoming_form(request, pk):
    """Set or change the expected availability date (custodian)."""
    from .forms import UpcomingForm
    asset = get_object_or_404(services.managed_by(request.user), pk=pk)
    form = UpcomingForm(request.POST or None, initial={"when": asset.expected_available_on, "note": asset.upcoming_note})
    if request.method == "POST" and form.is_valid():
        try:
            asset = services.set_expected_date(request.user, asset, form.cleaned_data["when"], form.cleaned_data["note"])
        except ValidationFailed as e:
            form.add_error(None, str(e))
        else:
            return with_toast(render(request, "catalogue/_panel.html", _panel_ctx(request, asset)),
                              _("%(name)s is listed as coming soon. People who asked will be told of changes.") % {"name": asset.name})
    return render(request, "catalogue/_upcoming_form.html", {"asset": asset, "form": form})


@needs("asset.publish")
@require_POST
def upcoming_cancel(request, pk):
    asset = get_object_or_404(services.managed_by(request.user), pk=pk)
    asset = services.cancel_expected_date(request.user, asset, request.POST.get("reason", ""))
    return with_toast(render(request, "catalogue/_panel.html", _panel_ctx(request, asset)),
                      _("Coming-soon listing cancelled. Interested people have been told."))


# ----------------------------------------------------------------------------- Phase 7: questions on an asset

def _qa_ctx(request, asset, error=""):
    return {"questions": services.questions_for_asset(asset), "can_ask": services.can_ask(request.user, asset),
            "can_answer": services.can_answer(request.user, asset), "qa_error": error, "asset": asset}


def _qa_reply(request, asset, toast="", error="", ok=True):
    resp = render(request, "catalogue/_qa.html", _qa_ctx(request, asset, error))
    return with_toast(resp, toast, ok=ok) if toast else resp


@login_required
@require_POST
def ask(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if not services.can_view(request.user, asset):
        raise Http404()
    try:
        services.ask_question(request.user, asset, request.POST.get("text", ""))
    except ValidationFailed as e:
        return _qa_reply(request, asset, error=str(e))
    return _qa_reply(request, asset, _("Question sent. The custodian has been told."))


@login_required
@require_POST
def answer(request, q_pk):
    from .models import AssetQuestion
    q = get_object_or_404(AssetQuestion.objects.select_related("asset"), pk=q_pk)
    if not services.can_answer(request.user, q.asset):
        raise Http404()
    try:
        services.answer_question(request.user, q, request.POST.get("text", ""))
    except ValidationFailed as e:
        if request.POST.get("from") == "list":
            return with_toast(HttpResponse(status=204), str(e), ok=False)
        return _qa_reply(request, q.asset, error=str(e))
    if request.POST.get("from") == "list":
        return with_toast(render(request, "catalogue/_questions_body.html", _questions_ctx(request)), _("Answer posted. The person who asked has been told."))
    return _qa_reply(request, q.asset, _("Answer posted. The person who asked has been told."))


@login_required
@require_POST
def withdraw(request, q_pk):
    from .models import AssetQuestion
    q = get_object_or_404(AssetQuestion.objects.select_related("asset"), pk=q_pk, asked_by=request.user)
    asset = q.asset
    try:
        services.withdraw_question(request.user, q)
    except ValidationFailed as e:
        return _qa_reply(request, asset, error=str(e))
    if request.POST.get("from") == "list":
        return with_toast(render(request, "catalogue/_questions_body.html", _questions_ctx(request)), _("Question withdrawn."))
    return _qa_reply(request, asset, _("Question withdrawn."))


def _questions_ctx(request):
    from .models import AssetQuestion
    return {"to_answer": services.questions_to_answer(request.user), "mine": AssetQuestion.objects.filter(asked_by=request.user)
            .select_related("asset", "answered_by").order_by("-asked_at")[:100], "stale_days": services.STALE_DAYS}


@login_required
def questions(request):
    """Phase 7: the custodian's questions to answer, and the person's own questions."""
    return render(request, "catalogue/questions.html", _questions_ctx(request))


# ----------------------------------------------------------------------------- Phase 8: bulk CSV import

@needs("asset.register")
def import_template(request):
    from . import bulk
    resp = HttpResponse(bulk.template_csv(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="circular-campus-assets-template.csv"'
    return resp


@needs("asset.register")
def import_start(request):
    """Upload a CSV. Nothing is registered at this step: it is checked and shown as a preview."""
    from django.shortcuts import redirect

    from . import bulk
    from .models import ImportBatch
    error = ""
    if request.method == "POST":
        upload = request.FILES.get("file")
        if upload is None:
            error = _("Choose a CSV file first.")
        else:
            try:
                batch = bulk.check_file(request.user, upload)
            except ValidationFailed as e:
                error = str(e)
            else:
                return redirect("catalogue:import_batch", pk=batch.pk)
    recent = ImportBatch.objects.filter(uploaded_by=request.user).order_by("-created_at")[:5]
    return render(request, "catalogue/import.html", {"error": error, "recent": recent, "columns": bulk.COLUMNS,
                                                     "required": bulk.REQUIRED, "max_rows": bulk.MAX_ROWS}, status=400 if error else 200)


@needs("asset.register")
def import_batch(request, pk):
    """Preview (before confirming) or result (after). Confirm and discard are POSTs to the same page."""
    from django.shortcuts import redirect

    from apps.common.errors import Forbidden

    from . import bulk
    from .models import ImportBatch, ImportStatus
    batch = get_object_or_404(ImportBatch, pk=pk, uploaded_by=request.user)
    error = ""
    if request.method == "POST":
        try:
            if request.POST.get("action") == "discard":
                bulk.discard(request.user, batch)
                return redirect("catalogue:import")
            keep = set(request.POST.getlist("keep"))
            skip = [r["n"] for r in batch.warning_rows if str(r["n"]) not in keep]
            batch = bulk.import_batch(request.user, batch.pk, skip_rows=skip, publish=request.POST.get("publish") == "1")
            return redirect("catalogue:import_batch", pk=batch.pk)
        except (ValidationFailed, Forbidden) as e:
            error = str(e)
            batch.refresh_from_db()
    return render(request, "catalogue/import_batch.html", {"batch": batch, "error": error, "done": batch.status == ImportStatus.IMPORTED,
                                                           "can_publish": batch.status == ImportStatus.PREVIEW and bulk.can_publish_all(request.user, batch)})
