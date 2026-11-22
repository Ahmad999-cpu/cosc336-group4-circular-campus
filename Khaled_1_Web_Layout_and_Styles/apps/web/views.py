from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse

from apps.access.permissions import has_any

from .context import _count, navigation


def _url(name):
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def home(request):
    """The start page: the statement band with the main ask, then shortcuts to what this person can do.
    Visitors who are not signed in get the public guest home page instead."""
    if not request.user.is_authenticated:
        from apps.guest.views import home as guest_home
        return guest_home(request)
    u = request.user
    shortcuts = []

    def add(perm, url_name, icon, title, text, count_path=None):
        url = _url(url_name)
        if url and (perm is None or has_any(u, perm)):
            shortcuts.append({"url": url, "icon": icon, "title": title, "text": text, "count": _count(count_path, u)})

    from django.utils.translation import gettext as _
    add("request.submit", "resource_requests:mine", "inbox", _("My requests"), _("Track what you asked for."), "apps.resource_requests.services:attention_count")
    add("asset.register", "catalogue:mine", "box", _("Our assets"), _("Register and publish what your unit no longer needs."))
    add("request.approve", "transfers:queue", "check", _("Approvals"), _("Requests waiting for your decision."), "apps.transfers.services:pending_count")
    add("transfer.dispatch", "transfers:board", "truck", _("Transfers"), _("Approved items to move."), "apps.transfers.services:to_dispatch_count")
    add("maintenance.record", "lifecycle:maintenance", "wrench", _("Maintenance"), _("Defects, inspections and repairs."))
    add(None, "sustainability:dashboard", "leaf", _("Impact"), _("What reuse has saved so far."))
    add("reports.view", "reporting:index", "chart", _("Reports"), _("Requests and transfers, with CSV and summary."))
    add(None, "catalogue:browse", "search", _("Browse"), _("Everything published for reuse right now."))
    return render(request, "web/home.html", {
        "find_url": _url("matching:find") or _url("catalogue:browse"),
        "can_request": has_any(u, "request.submit"),
        "shortcuts": shortcuts,
        "has_role": u.role_assignments.filter(active=True).exists(),
    })


@login_required
def badges(request):
    """Counts for the menu and the bell, fetched by app.js after an action (cc:refresh) and every minute,
    so badges don't go stale while someone works through a queue without reloading."""
    from apps.notifications.services import unread_count

    nav = navigation(request).get("nav_items", [])
    return JsonResponse({"nav": {i["key"]: i["count"] for i in nav}, "unread": unread_count(request.user)})


def csrf_failure(request, reason=""):
    """An expired page (usually after the session timed out): HTMX requests reload the page; others see 403."""
    if request.headers.get("HX-Request"):
        resp = HttpResponse(status=204)
        resp["HX-Refresh"] = "true"
        return resp
    return render(request, "403.html", status=403)
