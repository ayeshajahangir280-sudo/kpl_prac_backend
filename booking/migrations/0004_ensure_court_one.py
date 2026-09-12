from django.db import migrations


def ensure_court_one(apps, schema_editor):
    Court = apps.get_model("booking", "Court")
    Court.objects.get_or_create(court_number=1, defaults={"active": True})


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0003_create_initial_slots"),
    ]

    operations = [
        migrations.RunPython(ensure_court_one, migrations.RunPython.noop),
    ]