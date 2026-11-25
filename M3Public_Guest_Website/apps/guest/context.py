"""Values every template may use for the guest pages (kept here so a rename is one setting)."""
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse


def brand(request):
    return {
        "brand": settings.BRAND_NAME,
        "guest_cta_url": settings.GUEST_CTA_URL or reverse("access:login"),
        # Link previews (WhatsApp, LinkedIn, X) need an absolute image address.
        "og_image": request.build_absolute_uri(static("img/brand/og-image.jpg")),
    }
