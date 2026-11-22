"""C8 screens: the notifications page, opening one (marks it read), and mark all as read."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.web.htmx import is_htmx, redirect_htmx

from . import services

PAGE = 60


@login_required
def index(request):
    show = "unread" if request.GET.get("show") == "unread" else "all"
    notes = list(services.inbox(request.user, unread_only=show == "unread")[:PAGE])
    for n in notes:
        n.icon = services.ICON.get(n.event_type, "bell")
    return render(request, "notifications/index.html", {
        "groups": services.grouped(notes), "show": show, "unread": services.unread_count(request.user),
        "labels": {"today": _("Today"), "yesterday": _("Yesterday"), "earlier": _("Earlier")}})


@login_required
def open_note(request, pk):
    n = services.mark_read(request.user, pk)
    return redirect(services.target_url(n, request.user))


@login_required
@require_POST
def read_all(request):
    services.mark_all_read(request.user)
    nxt = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if not nxt.startswith("/"):
        nxt = "/"
    return redirect_htmx(nxt) if is_htmx(request) else redirect(nxt)
