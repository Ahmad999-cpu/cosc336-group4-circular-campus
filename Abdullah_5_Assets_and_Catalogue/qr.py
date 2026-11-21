"""QR labels for assets (Feature 1).

The code holds only the asset's address (a stable URL with the asset id). Opening it goes through the normal
asset page, which needs a sign-in and applies `services.can_view`, so a label never bypasses access control and
never carries the name, value, owner or anything else about the asset.

Library: segno (pure Python, no other dependencies). Base URL: settings.SITE_BASE_URL, so printed labels point to
the real server; if it is empty we fall back to the address the current request came in on (fine on a laptop,
wrong for printed labels: the label page warns about this).
"""
from __future__ import annotations

import re
from xml.sax.saxutils import escape

from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

ERROR_LEVEL = "m"  # survives about 15 % damage: a scratched sticker still scans


def asset_path(asset) -> str:
    return reverse("catalogue:panel", args=[asset.pk])


def base_url_configured() -> bool:
    return bool(getattr(settings, "SITE_BASE_URL", ""))


def asset_url(asset, request=None) -> str:
    """Absolute address encoded in the code. Never a hard-coded host."""
    path = asset_path(asset)
    base = (getattr(settings, "SITE_BASE_URL", "") or "").rstrip("/")
    if base:
        return base + path
    if request is not None:
        return request.build_absolute_uri(path)
    raise ValueError("SITE_BASE_URL is not set and there is no request to take the address from")


def short_id(asset) -> str:
    """First 8 characters of the id, printed under the code so a person can read it out or type it."""
    return str(asset.pk).split("-")[0].upper()


def _modules(url: str) -> tuple[str, int]:
    """The QR symbol as one SVG path (drawn at 1 unit per module, no quiet zone) and its size in modules."""
    import segno  # imported here so the rest of the app loads even if the package is missing

    q = segno.make(url, error=ERROR_LEVEL, micro=False)
    svg = q.svg_inline(scale=1, border=0)
    d = re.search(r'\sd="([^"]+)"', svg).group(1)
    return d, q.symbol_size(scale=1, border=0)[0]


def code_svg(url: str, px: int = 240) -> str:
    """Just the code, for showing on screen."""
    d, n = _modules(url)
    quiet = 4
    size = n + 2 * quiet
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{px}" height="{px}" '
            f'role="img" aria-hidden="true" shape-rendering="crispEdges"><rect width="{size}" height="{size}" fill="#fff"/>'
            f'<path transform="translate({quiet} {quiet})" stroke="#000" d="{d}"/></svg>')


def label_svg(asset, url: str, *, scan_hint: str, id_label: str) -> str:
    """A printable label: the code plus the asset name, category, owning unit and short id, so the sticker (and
    the downloaded file) says which asset it belongs to. Only descriptive text that is already on the item."""
    d, n = _modules(url)
    quiet, scale = 4, 6
    code = (n + 2 * quiet) * scale
    width = code + 330
    height = max(code, 230)

    def t(x, y, text, size, weight=400, fill="#0E1F3A"):
        return (f'<text x="{x}" y="{y}" font-family="Archivo, Arial, sans-serif" font-size="{size}" font-weight="{weight}" '
                f'fill="{fill}">{escape(text)}</text>')

    name = asset.name if len(asset.name) <= 30 else asset.name[:29] + "…"
    lines = [
        t(code + 10, 46, name, 22, 700),
        t(code + 10, 76, asset.category.name[:40], 15, 400, "#4A5B73"),
        t(code + 10, 104, str(asset.owner_department)[:40], 15, 400, "#4A5B73"),
        t(code + 10, 150, f"{id_label} {short_id(asset)}", 18, 700),
        t(code + 10, 186, scan_hint[:48], 13, 400, "#4A5B73"),
    ]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<title>{escape(asset.name)} ({short_id(asset)})</title>'
            f'<rect width="{width}" height="{height}" rx="14" fill="#fff" stroke="#0E1F3A" stroke-width="2"/>'
            f'<g transform="translate(0 {(height - code) // 2})" shape-rendering="crispEdges">'
            f'<path transform="translate({quiet * scale} {quiet * scale}) scale({scale})" stroke="#000" d="{d}"/></g>'
            + "".join(lines) + "</svg>")


def download_name(asset) -> str:
    return f"asset-{short_id(asset).lower()}-{slugify(asset.name)[:40] or 'label'}.svg"
