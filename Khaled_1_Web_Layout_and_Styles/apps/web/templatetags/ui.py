"""Template tags shared by every module: icons, score ring, status pill, money, empty states.

Usage:  {% load ui %}  {% icon "monitor" 44 %}  {% ring 91 %}  {{ value|aed }}  {% pill "ok" "Suitable" %}
"""
import json
import math
from decimal import Decimal

from django import template
from django.contrib.messages import get_messages
from django.utils.formats import number_format
from django.utils.html import format_html, mark_safe
from django.utils.translation import get_language, gettext as _

register = template.Library()

# Stroke icons (24 x 24). Add new ones here so every module draws the same set.
ICONS = {
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "chair": '<path d="M7 3h10v8H7z"/><path d="M5 11h14v3H5zM7 14v7M17 14v7"/>',
    "stool": '<ellipse cx="12" cy="6" rx="7" ry="2.5"/><path d="M7 8l-2 13M17 8l2 13M8.5 15h7"/>',
    "scope": '<rect x="3" y="5" width="18" height="13" rx="2"/><path d="M6 13l3-4 3 6 3-5 3 3"/>',
    "printer": '<path d="M5 4h14v4H5z"/><path d="M4 8h16v10H4z"/><path d="M9 18v2h6v-2M12 8v5"/>',
    "board": '<rect x="3" y="3" width="18" height="12" rx="1"/><path d="M8 15l-2 6M16 15l2 6M8 8h6M8 11h3"/>',
    "power": '<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="8" cy="12" r="2"/><path d="M14 10h4M14 14h4"/>',
    "dock": '<rect x="4" y="9" width="16" height="7" rx="2"/><path d="M7 12h1M10 12h1M14 12h3"/>',
    "projector": '<rect x="2" y="8" width="20" height="9" rx="2"/><circle cx="15" cy="12.5" r="2.5"/><path d="M6 12h3M7 17v2M17 17v2"/>',
    "shelf": '<path d="M5 3v18M19 3v18M5 8h14M5 13h14M5 18h14"/>',
    "laptop": '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 19h20"/>',
    "box": '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7M12 11v10"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
    "check": '<path d="M5 12l5 5L20 7"/>',
    "logout": '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l-5-5 5-5M5 12h11"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "truck": '<path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "qr": '<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z"/><path d="M14 14h2v2h-2zM18 14h2M14 18v2h2M18 18h2v2"/>',
    "sprout": '<path d="M12 21v-9"/><path d="M12 12C12 7.6 8.9 5 4 5c0 4.4 3.1 7 8 7z"/><path d="M12 14c0-3.9 2.7-6.2 7.5-6.2 0 3.9-2.7 6.2-7.5 6.2z"/>',
    "leaf": '<path d="M5 21c0-9 5-15 15-16-1 10-7 15-16 15"/><path d="M5 21l8-8"/>',
    "inbox": '<path d="M3 13l3-8h12l3 8v6H3z"/><path d="M3 13h5l1 2h6l1-2h5"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "spark": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "upload": '<path d="M12 20V9M7 14l5-5 5 5M5 4h14"/>',
    "download": '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    "alert": '<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17.5v.5"/>',
}


@register.simple_tag
def icon(name, size=20, color="currentColor", width="1.8"):
    path = ICONS.get(name, ICONS["box"])
    return format_html(
        '<svg width="{0}" height="{0}" viewBox="0 0 24 24" fill="none" stroke="{1}" stroke-width="{2}" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{3}</svg>',
        size, color, width, mark_safe(path),
    )


@register.simple_tag
def ring(score, size=76, weak_below=70):
    """Score ring 0-100. The arc starts empty and app.js fills it (no motion if reduced motion is set)."""
    try:
        score = max(0, min(100, float(score)))
    except (TypeError, ValueError):
        score = 0
    r = size / 2 - 6
    c = 2 * math.pi * r
    color = "var(--navy)" if score >= weak_below else "var(--warn-ring)"
    return format_html(
        '<div class="ring" style="width:{0}px;height:{0}px"><svg width="{0}" height="{0}" viewBox="0 0 {0} {0}" aria-hidden="true">'
        '<circle class="track" cx="{1}" cy="{1}" r="{2}" fill="none" stroke-width="7"/>'
        '<circle class="val" cx="{1}" cy="{1}" r="{2}" fill="none" stroke="{3}" stroke-width="7" stroke-linecap="round" '
        'stroke-dasharray="{4}" stroke-dashoffset="{4}" data-to="{5}"/></svg>'
        '<b class="tnum">{6}</b><span class="sr">{7}</span></div>',
        size, size / 2, r, color, f"{c:.1f}", f"{c * (1 - score / 100):.1f}", int(round(score)), _("fit score"),
    )


@register.simple_tag
def pill(kind, text):
    return format_html('<span class="pill {}">{}</span>', kind, text)


@register.filter
def aed(value):
    """Money in AED, localised digits and separators. None shows as 'unavailable' (never 0)."""
    if value is None or value == "":
        return _("unavailable")
    amount = number_format(Decimal(value).quantize(Decimal("1")), 0, force_grouping=True)
    return f"{amount} درهم" if (get_language() or "").startswith("ar") else f"AED {amount}"


@register.filter
def num(value, decimals=0):
    if value is None or value == "":
        return _("unavailable")
    return number_format(value, int(decimals), force_grouping=True)


@register.inclusion_tag("components/empty.html")
def empty_state(title, text="", action_url="", action_label="", style="btn-navy"):
    return {"title": title, "text": text, "action_url": action_url, "action_label": action_label, "style": style}


@register.simple_tag(takes_context=True)
def flash_messages(context):
    """Django messages become toasts (see app.js). Each message may carry 'href|label' in extra_tags."""
    request = context.get("request")
    if request is None:
        return ""
    items = []
    for m in get_messages(request):
        href = label = ""
        tags = (m.extra_tags or "").split()
        celebrate = "celebrate" in tags
        link = next((t for t in tags if "|" in t), "")
        if link:
            href, label = link.split("|", 1)
        items.append({"text": str(m), "level": m.level_tag, "href": href, "label": label, "celebrate": celebrate})
    if not items:
        return ""
    data = json.dumps(items).replace("</", "<\\/")
    return mark_safe(f'<script type="application/json" data-flash>{data}</script>')


@register.simple_tag
def steps(status, labels):
    """Request progress: labels = 'Sent,Approved,On its way,Received'; status index 0-3, -1 = closed."""
    names = [s.strip() for s in str(labels).split(",")]
    try:
        idx = int(status)
    except (TypeError, ValueError):
        idx = -1
    out = []
    for i, name in enumerate(names):
        cls = "done" if i < idx or (idx == len(names) - 1 and i == idx) else "now" if i == idx else ""
        delay = f' style="--d:{i * 0.12:.2f}s"' if cls else ""
        out.append(format_html('<div class="step {}"><div class="bar"><i{}></i></div>{}</div>', cls, mark_safe(delay), name))
    return format_html('<div class="steps">{}</div>', mark_safe("".join(out)))


@register.filter
def get(mapping, key):
    """dict lookup in templates: {{ d|get:k }}."""
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def percent(value):
    """0-1 as a whole percentage, e.g. 0.875 -> 88%."""
    if value in (None, ""):
        return _("unavailable")
    return f"{number_format((Decimal(str(value)) * 100).quantize(Decimal('1')), 0)}%"


@register.simple_tag
def factor_label(key):
    """Human label for a matching factor (f1..f8)."""
    from apps.matching.engine import FACTOR_LABELS
    return FACTOR_LABELS.get(key, key)


@register.filter
def tr(value):
    """Translate a message that came from a service (e.g. a DomainError) in the reader's language."""
    from django.utils.translation import gettext
    return gettext(str(value)) if value not in (None, "") else ""
