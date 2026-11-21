"""Screens of the Matching module: the Find page and suggestions on a saved request (AI feature 2)."""
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.access.permissions import has_any
from apps.catalogue.models import Category
from apps.common.enums import UserDecision
from apps.common.errors import ValidationFailed
from apps.resource_requests.models import RequestStatus, ResourceRequest
from apps.web.htmx import is_htmx, redirect_htmx, with_toast

from . import services
from .engine import guess_quantity
from .models import MatchRecommendation

EXAMPLES = {
    "en": ["Two 24-inch monitors for the robotics club workstation", "Ten chairs for a seminar room this month",
           "Bench power supply for an electronics lab", "شاشتان مقاس 24 بوصة لنادي الروبوتات"],
    "ar": ["شاشتان مقاس 24 بوصة لنادي الروبوتات", "عشرة كراسي لقاعة ندوات هذا الشهر", "مزود طاقة لمختبر إلكترونيات",
           "Two 24-inch monitors for the robotics club"],
}


def _qty(request, q: str) -> tuple[int, bool]:
    """The stepper wins if the person moved it; otherwise a number in the words ('two monitors') is used."""
    try:
        qty = max(1, min(999, int(request.GET.get("qty") or 1)))
    except ValueError:
        qty = 1
    if qty == 1:
        guessed = guess_quantity(q)
        if guessed and 1 < guessed <= 999:
            return guessed, True
    return qty, False


@needs("request.submit")
def find(request):
    """UC-26 from the Find page: describe a need in English or Arabic and get ranked, explained matches."""
    q = (request.GET.get("q") or "").strip()[:500]
    qty, guessed = _qty(request, q)
    category = None
    if request.GET.get("category"):
        category = Category.objects.filter(pk=request.GET["category"]).first() if len(request.GET["category"]) == 36 else None
    lang = "ar" if (get_language() or "").startswith("ar") else "en"
    ctx = {"q": q, "qty": qty, "examples": EXAMPLES[lang], "outcome": None, "category": category,
           "reasons": services.NOT_SUITABLE_REASONS, "guessed": guessed}
    if q:
        try:
            ctx["outcome"] = services.find(q, request.user, qty, category)
        except ValidationFailed as e:
            ctx["error"] = str(e)
    if is_htmx(request) and request.headers.get("HX-Target") == "results":
        return render(request, "matching/_results.html", ctx)
    return render(request, "matching/find.html", ctx)


def _rec_for(request, pk) -> MatchRecommendation:
    rec = get_object_or_404(MatchRecommendation.objects.select_related("result_set__request", "asset"), pk=pk)
    rs = rec.result_set
    owner = rs.request.requester_id if rs.request_id else rs.generated_by_id
    if owner != request.user.pk:
        raise Http404()
    return rec


@needs("request.submit")
@require_POST
def not_for_me(request, pk):
    """'Not for me' with a reason chip. The card fades out; the reason is kept for tuning (Section 9.7)."""
    rec = _rec_for(request, pk)
    services.record_decision(rec.pk, request.user, UserDecision.REJECTED, request.POST.get("reason", ""))
    return with_toast(HttpResponse(""), _("Thanks. We'll show fewer like that."))


@needs("request.submit")
def for_request(request, pk):
    """Suggested items inside a pending request's panel (loaded lazily)."""
    req = get_object_or_404(ResourceRequest.objects.select_related("category", "department", "selected_asset"), pk=pk)
    if req.requester_id != request.user.pk:
        raise Http404()
    outcome = services.suggestions_for(req, request.user) if req.status == RequestStatus.PENDING_APPROVAL else None
    return render(request, "matching/_for_request.html", {"req": req, "outcome": outcome, "reasons": services.NOT_SUITABLE_REASONS})


@needs("request.submit")
@require_POST
def choose(request, pk):
    rec = _rec_for(request, pk)
    req = services.choose_for_request(rec.pk, request.user)
    # A new query string makes the browser reload even when it is already on My requests.
    resp = redirect_htmx(reverse("resource_requests:mine") + f"?picked={req.pk}#r-{req.pk}")
    messages.success(request, _("%(name)s selected. Your request can now be approved.") % {"name": rec.asset.name})
    return resp


def procure(request):
    """Feature 3: check the catalogue before buying. Lists alternatives; never requests or reserves anything."""
    from django.contrib.auth.views import redirect_to_login
    from django.core.exceptions import PermissionDenied

    from . import procurement
    from .forms import ProcurementForm
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not procurement.may_check(request.user):
        raise PermissionDenied()
    d = request.user.department
    form = ProcurementForm(request.GET or None, initial={"campus": (d.campus if d else "") or ""})
    ctx = {"form": form, "res": None, "can_request": has_any(request.user, "request.submit")}
    if request.GET and form.is_valid():
        c = form.cleaned_data
        plan = procurement.Plan(description=c["description"], quantity=c["quantity"], category=c["category"],
                                specifications=c["specifications"], condition=c["condition"] or "ANY", campus=c["campus"],
                                needed_by=c["needed_by"], unit_price=c["unit_price"])
        try:
            ctx["res"] = procurement.check(request.user, plan)
        except ValidationFailed as e:
            form.add_error(None, str(e))
    if is_htmx(request) and request.headers.get("HX-Target") == "proc-out":
        return render(request, "matching/_procure_out.html", ctx)
    return render(request, "matching/procure.html", ctx)


# ----------------------------------------------------------------------------- Phase 5: saved needs

def _need_for(request, pk):
    from .models import SavedNeed
    need = get_object_or_404(SavedNeed.objects.select_related("category", "asset", "department"), pk=pk)
    if need.owner_id != request.user.pk:
        raise Http404()  # someone else's need: as if it did not exist
    return need


def _needs_ctx(request):
    from . import wishlist
    needs = list(wishlist.mine(request.user))
    for n in needs:
        n.current = wishlist.current_matches(n)
    from django.utils import timezone
    return {"needs": [n for n in needs if not n.is_interest], "interests": [n for n in needs if n.is_interest],
            "can_request": has_any(request.user, "request.submit"), "today_ymd": timezone.localdate().strftime("%Y%m%d")}


@needs("request.submit")
def saved(request):
    """Phase 5: my saved needs, what currently fits each one, and the controls."""
    ctx = _needs_ctx(request)
    if is_htmx(request) and request.headers.get("HX-Target") == "needs":
        return render(request, "matching/_needs.html", ctx)
    return render(request, "matching/saved.html", ctx)


def _need_reply(request, text):
    resp = render(request, "matching/_needs.html", _needs_ctx(request))
    resp["HX-Retarget"] = "#needs"
    resp["HX-Reswap"] = "innerHTML"
    return with_toast(resp, text, close_drawer=True)


@needs("request.submit")
def need_form(request, pk=None):
    from . import wishlist
    from .forms import SavedNeedForm
    need = _need_for(request, pk) if pk else None
    if need is not None and need.is_interest:
        raise Http404()
    d = request.user.department
    initial = {k: getattr(need, k) for k in wishlist.FIELDS} if need else {
        "description": request.GET.get("q", "")[:300], "quantity": request.GET.get("qty") or 1, "campus": (d.campus if d else "") or ""}
    form = SavedNeedForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        try:
            if need:
                need, found = wishlist.update_need(request.user, need, data)
            else:
                need, found = wishlist.save_need(request.user, data)
        except ValidationFailed as e:
            form.add_error(None, str(e))
        else:
            n = len(found)
            if request.POST.get("from") != "list":
                messages.success(request, _("Saved. We'll tell you when something that fits is published."))
                return redirect_htmx(reverse("matching:saved"))
            return _need_reply(request, _("Saved. %(n)s item(s) already fit; we'll tell you about new ones.") % {"n": n} if n
                               else _("Saved. We'll tell you when something that fits is published."))
    return render(request, "matching/_need_form.html", {"form": form, "need": need, "from_list": request.GET.get("from") == "list" or request.POST.get("from") == "list"})


@needs("request.submit")
@require_POST
def need_action(request, pk, action):
    from . import wishlist
    need = _need_for(request, pk)
    if action == "deactivate":
        wishlist.set_active(request.user, need, False)
        return _need_reply(request, _("Deactivated. No more alerts for this need."))
    if action == "activate":
        need = wishlist.set_active(request.user, need, True)
        found = wishlist.check_need(need, notify=False)
        return _need_reply(request, _("Active again. %(n)s item(s) fit right now.") % {"n": len(found)})
    if action == "delete":
        wishlist.delete_need(request.user, need)
        return _need_reply(request, _("Deleted."))
    if action == "check":
        found = wishlist.check_need(need, notify=False)
        if need.check_failed:
            return _need_reply(request, _("Matching is unavailable right now. Your need is kept; try again later."))
        return _need_reply(request, _("Checked: %(n)s item(s) fit right now.") % {"n": len(found)})
    raise Http404()



@needs("request.submit")
@require_POST
def interest(request, pk):
    """Phase 6: 'Tell me when it's ready' on a coming-soon item. Answers with the refreshed item panel."""
    from apps.catalogue.models import Asset
    from apps.catalogue.views import _panel_ctx  # the item panel is Catalogue's; reuse its context

    from . import wishlist
    asset = get_object_or_404(Asset.objects.select_related("category", "owner_department", "custodian"), pk=pk)
    try:
        wishlist.express_interest(request.user, asset)
    except ValidationFailed as e:
        return with_toast(HttpResponse(""), str(e), ok=False)
    return with_toast(render(request, "catalogue/_panel.html", _panel_ctx(request, asset)),
                      _("Done. You'll be told when it is ready or if the date changes. This is not a reservation."))
