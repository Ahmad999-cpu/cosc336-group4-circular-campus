"""Small helpers for views that answer HTMX requests."""
import json

from django.http import HttpResponse


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def with_toast(response: HttpResponse, text: str, ok: bool = True, href: str = "", label: str = "",
               close_drawer: bool = False) -> HttpResponse:
    """Ask the page to show a toast (and optionally close the side panel) after the swap.
    app.js listens for the cc:toast and cc:close-drawer events that HTMX fires from HX-Trigger."""
    events = {"cc:toast": {"text": str(text), "ok": ok, "href": href, "label": str(label)}, "cc:refresh": True}
    if close_drawer:
        events["cc:close-drawer"] = True
    response["HX-Trigger-After-Settle"] = json.dumps(events)
    return response


def redirect_htmx(url: str) -> HttpResponse:
    """Full-page redirect from an HTMX request."""
    r = HttpResponse(status=204)
    r["HX-Redirect"] = url
    return r
