from django.apps import AppConfig


class SustainabilityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sustainability"
    label = "sustainability"
    verbose_name = "Sustainability"

    def ready(self):
        from . import receivers  # noqa: F401
