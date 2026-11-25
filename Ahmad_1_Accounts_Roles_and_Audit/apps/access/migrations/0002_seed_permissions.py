"""Every install needs the permission codes that services check (access.models.PERMISSIONS)."""
from django.db import migrations


def seed(apps, schema_editor):
    from apps.access.models import PERMISSIONS

    Permission = apps.get_model("access", "Permission")
    for code, desc in PERMISSIONS.items():
        Permission.objects.update_or_create(code=code, defaults={"description": desc})


class Migration(migrations.Migration):
    dependencies = [("access", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
