import os
from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from booking.models import Booking, Court, Slot, User


class Command(BaseCommand):
    help = "Seed admin account, courts, and the initial September 2026 slots."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin12345")
        UserModel = get_user_model()
        admin, created = UserModel.objects.get_or_create(
            username=username,
            defaults={"email": email, "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        admin.email = email
        admin.role = User.Role.ADMIN
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(password)
        admin.save()

        desired_slots = [
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
        court_numbers = sorted({court_number for _, court_number, _, _ in desired_slots})
        courts = {
            number: Court.objects.get_or_create(court_number=number, defaults={"active": True})[0]
            for number in court_numbers
        }
        Court.objects.exclude(court_number__in=court_numbers).update(active=False)

        desired_slot_ids = []
        count = 0
        for slot_date, court_number, start_time, end_time in desired_slots:
            slot, made = Slot.objects.get_or_create(
                date=slot_date,
                court=courts[court_number],
                start_time=start_time,
                end_time=end_time,
                defaults={"active": True},
            )
            if not slot.active:
                slot.active = True
                slot.save(update_fields=["active"])
            desired_slot_ids.append(slot.id)
            count += int(made)

        extra_slots = Slot.objects.exclude(id__in=desired_slot_ids)
        booked_extra_slot_ids = Booking.objects.filter(
            slot__in=extra_slots,
            status=Booking.Status.CONFIRMED,
        ).values_list("slot_id", flat=True)
        extra_slots.exclude(id__in=booked_extra_slot_ids).delete()
        extra_slots.filter(id__in=booked_extra_slot_ids).update(active=False)
        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. {action} admin account, created {count} new slots. Admin username: {username}"
            )
        )
