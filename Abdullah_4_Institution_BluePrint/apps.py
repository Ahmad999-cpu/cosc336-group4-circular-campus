from django.apps import AppConfig


class BlueprintConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blueprint"
    label = "blueprint"
    verbose_name = "Institution Blueprint"
