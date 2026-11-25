"""Guest pages. Public on purpose: no sign-in, no session created, nothing from the signed-in app is shown."""
from django.conf import settings
from django.contrib.staticfiles import finders
from django.shortcuts import redirect, render
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from . import blueprint_demo, pricing, services
from .forms import ContactForm, stamp


def _video():
    """The home video: a static file (under static/), a full URL, or None for the placeholder."""
    v = settings.GUEST_HOME_VIDEO
    if not v:
        return None
    if v.startswith(("https://", "http://", "/")):
        return {"src": v, "poster": settings.GUEST_HOME_VIDEO_POSTER}
    if finders.find(v):
        from django.templatetags.static import static
        poster = settings.GUEST_HOME_VIDEO_POSTER
        return {"src": static(v), "poster": static(poster) if poster and not poster.startswith("http") else poster}
    return None


def home(request):
    if request.user.is_authenticated:
        return redirect("web:home")
    return render(request, "guest/home.html", {"video": _video(), "page": "home"})


def pricing_page(request):
    """Pricing: its own page (institution type picker, VAT toggle, the 10,000+ staff band)."""
    return render(request, "guest/pricing.html", {"page": "pricing",
                                                  "pricing": pricing.context(request.GET.get("type"), request.GET.get("vat") == "1")})


def blueprint(request):
    """Institution Blueprint: its own page, with the interactive template preview."""
    return render(request, "guest/blueprint.html", {"page": "blueprint", "blueprint": blueprint_demo.context(request.GET.get("bp"))})


def how_it_works(request):
    return render(request, "guest/how.html", {"page": "how"})


@require_http_methods(["GET", "POST"])
def contact(request):
    ctx = {"page": "contact", "phone": settings.CONTACT_PHONE, "email": settings.CONTACT_EMAIL, "state": None}
    if request.method == "POST":
        form = ContactForm(request.POST)
        spam = form.spam_check()
        if spam == "honeypot":
            ctx["state"] = "discarded"
        elif spam:
            ctx["state"] = "retry"
            form = ContactForm(initial={k: request.POST.get(k, "") for k in ("name", "email", "organisation", "phone", "message")} | {"started": stamp()})
        elif form.is_valid():
            key = services.visitor_key(request.META.get("REMOTE_ADDR", ""))
            if services.rate_limited(key):
                ctx["state"] = "limited"
            else:
                msg = services.deliver(form.cleaned_data, ip_key=key, language=get_language() or "")
                ctx["state"] = {"SENT": "sent", "NOT_CONFIGURED": "saved", "FAILED": "failed"}[msg.delivery]
                if ctx["state"] == "sent":
                    form = ContactForm(initial={"started": stamp()})
        else:
            ctx["state"] = "invalid"
            for name in form.errors:  # screen readers hear which field is wrong and why
                if name in form.fields:
                    form.fields[name].widget.attrs.update({"aria-invalid": "true", "aria-describedby": f"id_{name}-err"})
    else:
        form = ContactForm(initial={"started": stamp()})
    ctx["form"] = form
    if request.headers.get("HX-Request"):
        return render(request, "guest/_contact_form.html", ctx)
    return render(request, "guest/contact.html", ctx)


# ---------- Search engines ----------
# Only the public pages are listed; everything behind sign-in is kept out of search results.
PUBLIC_PAGES = ["web:home", "guest:how", "guest:blueprint", "sustainability:calculator", "guest:pricing", "guest:contact"]
PRIVATE_PREFIXES = ["/admin/", "/accounts/", "/assets/", "/requests/", "/approvals/", "/lifecycle/", "/find/",
                    "/reports/", "/notifications/", "/audit/", "/ai/", "/setup/"]


@require_http_methods(["GET", "HEAD"])
def robots_txt(request):
    from django.http import HttpResponse
    from django.urls import reverse

    lines = ["User-agent: *"]
    lines += [f"Disallow: {p}" for p in PRIVATE_PREFIXES]
    lines += ["Disallow: /impact/", f"Allow: {reverse('sustainability:calculator')}", "",
              f"Sitemap: {request.build_absolute_uri(reverse('guest:sitemap'))}", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_http_methods(["GET", "HEAD"])
def sitemap_xml(request):
    from django.http import HttpResponse
    from django.urls import reverse
    from django.utils.html import escape

    urls = "".join(f"  <url><loc>{escape(request.build_absolute_uri(reverse(n)))}</loc></url>\n" for n in PUBLIC_PAGES)
    body = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'
    return HttpResponse(body, content_type="application/xml; charset=utf-8")


@require_http_methods(["GET", "HEAD"])
def favicon_ico(request):
    """Browsers also ask for /favicon.ico at the site root; point them at the real file."""
    from django.http import HttpResponsePermanentRedirect
    from django.templatetags.static import static

    return HttpResponsePermanentRedirect(static("img/brand/favicon.ico"))
