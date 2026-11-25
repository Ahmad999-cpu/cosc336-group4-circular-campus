from django.apps import AppConfig


class LifecycleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lifecycle"
    label = "lifecycle"
    verbose_name = "Life Cycle & Maintenance"

    def ready(self):
        from . import receivers  # noqa: F401  (connects the asset history listener)
