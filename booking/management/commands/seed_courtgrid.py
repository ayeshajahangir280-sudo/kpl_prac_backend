import os
from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from booking.models import Court, Slot, User


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

        courts = [Court.objects.get_or_create(court_number=number, defaults={"active": True})[0] for number in (2, 3, 4)]
        slot_days = [date(2026, 9, 16), date(2026, 9, 17)]
        times = [(time(21, 0), time(22, 0)), (time(22, 0), time(23, 0)), (time(23, 0), time(0, 0))]
        count = 0
        for slot_date in slot_days:
            for court in courts:
                for start_time, end_time in times:
                    _, made = Slot.objects.get_or_create(
                        date=slot_date,
                        court=court,
                        start_time=start_time,
                        end_time=end_time,
                        defaults={"active": True},
                    )
                    count += int(made)
        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. {action} admin account, created {count} new slots. Admin username: {username}"
            )
        )
