from django.apps import AppConfig


class AccessConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.access"
    label = "access"
    verbose_name = "Users & Access"

    def ready(self):
        from . import receivers  # noqa: F401  (audit of sign-in events)
