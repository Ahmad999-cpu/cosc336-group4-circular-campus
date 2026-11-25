from django.apps import AppConfig


class GuestConfig(AppConfig):
    """Public pages for visitors who are not signed in: home, how it works, contact."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.guest"
    verbose_name = "Guest site"
