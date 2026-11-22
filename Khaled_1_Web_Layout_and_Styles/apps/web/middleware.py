"""Turns business-rule refusals into clear feedback instead of a server error.

A service raises Forbidden -> 403 page. Any other DomainError -> the message as a toast, and the person
stays on the page they came from. HTMX requests get the toast through HX-Trigger.
"""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, resolve_url
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.common.errors import DomainError, Forbidden

from .htmx import is_htmx, with_toast

FRIENDLY = {
    "SELF_APPROVAL": _("You can't decide your own request. Another approver must."),
    "INSUFFICIENT_QUANTITY": _("Not enough free units left. Someone else's approval took them."),
    "CONFLICT": _("This changed while you were looking at it. The page has been refreshed."),
    "NOT_PENDING": _("This request has already been decided."),
}


class DomainErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exc):
        if isinstance(exc, Forbidden):
            raise PermissionDenied(gettext(str(exc)))
        if not isinstance(exc, DomainError):
            return None
        # Service messages are collected by our makemessages (keywords ValidationFailed, Forbidden…) and
        # translated here, at display time, in the reader's language.
        text = str(FRIENDLY.get(exc.code) or gettext(str(exc)))
        if is_htmx(request):
            resp = HttpResponse(status=204)
            resp["HX-Reswap"] = "none"
            return with_toast(resp, text, ok=False)
        messages.error(request, text)
        return redirect(request.META.get("HTTP_REFERER") or "/")


class HtmxEdgeMiddleware:
    """Keeps partial-page requests sensible at the edges (found in the validation loop):

    * signed out (the 15-minute timeout) -> the whole page goes to sign-in, instead of the sign-in form
      appearing inside a side panel;
    * not allowed (403) -> a toast, instead of the 403 page inside a table cell.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not is_htmx(request):
            return response
        location = response.get("Location", "")
        login = resolve_url(settings.LOGIN_URL)
        if response.status_code in (301, 302) and location.startswith(login):
            back = request.headers.get("HX-Current-URL", "")
            path = back.split("//", 1)[-1].split("/", 1)[-1] if back else ""
            out = HttpResponse(status=204)
            out["HX-Redirect"] = f"{login}?{urlencode({'next': '/' + path})}" if path else login
            return out
        if response.status_code == 403:
            out = HttpResponse(status=204)
            out["HX-Reswap"] = "none"
            return with_toast(out, _("You don't have access to this"), ok=False)
        return response
