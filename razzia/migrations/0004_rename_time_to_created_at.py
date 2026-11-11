from django.db import migrations, models
from django.utils import timezone


def fill_null_created_at(apps, schema_editor):
    # Rows that had time=NULL would break the NOT NULL alter below.
    Model = apps.get_model("razzia", "RazziaEntry")
    Model.objects.filter(created_at__isnull=True).update(created_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ("razzia", "0003_razzia_created_at_razzia_updated_at"),  # <- your previous migration
    ]

    operations = [
        migrations.RenameField(
            model_name="RazziaEntry",
            old_name="time",
            new_name="created_at",
        ),
        migrations.RunPython(fill_null_created_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="RazziaEntry",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]