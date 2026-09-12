from datetime import date, time

from django.db import migrations


INITIAL_SLOTS = [
    (date(2026, 9, 16), 2, time(21, 0), time(22, 0)),
    (date(2026, 9, 16), 2, time(22, 0), time(23, 0)),
    (date(2026, 9, 16), 2, time(23, 0), time(0, 0)),
    (date(2026, 9, 16), 3, time(21, 0), time(22, 0)),
    (date(2026, 9, 16), 3, time(22, 0), time(23, 0)),
    (date(2026, 9, 16), 3, time(23, 0), time(0, 0)),
    (date(2026, 9, 16), 4, time(21, 0), time(22, 0)),
    (date(2026, 9, 16), 4, time(22, 0), time(23, 0)),
    (date(2026, 9, 16), 4, time(23, 0), time(0, 0)),
    (date(2026, 9, 17), 2, time(20, 0), time(21, 0)),
    (date(2026, 9, 17), 2, time(22, 0), time(23, 0)),
    (date(2026, 9, 17), 3, time(20, 0), time(21, 0)),
    (date(2026, 9, 17), 4, time(20, 0), time(21, 0)),
    (date(2026, 9, 17), 1, time(20, 0), time(21, 0)),
    (date(2026, 9, 17), 1, time(21, 0), time(22, 0)),
    (date(2026, 9, 17), 1, time(22, 0), time(23, 0)),
    (date(2026, 9, 17), 1, time(23, 0), time(0, 0)),
]


def create_initial_slots(apps, schema_editor):
    Court = apps.get_model("booking", "Court")
    Slot = apps.get_model("booking", "Slot")
    courts = {
        number: Court.objects.get_or_create(court_number=number, defaults={"active": True})[0]
        for number in sorted({court_number for _, court_number, _, _ in INITIAL_SLOTS})
    }
    for slot_date, court_number, start_time, end_time in INITIAL_SLOTS:
        Slot.objects.get_or_create(
            date=slot_date,
            court=courts[court_number],
            start_time=start_time,
            end_time=end_time,
            defaults={"active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0002_alter_user_groups"),
    ]

    operations = [
        migrations.RunPython(create_initial_slots, migrations.RunPython.noop),
    ]
