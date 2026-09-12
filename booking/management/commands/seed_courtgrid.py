import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from booking.models import User


class Command(BaseCommand):
    help = "Create or reset the default admin account."

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

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"Seed complete. {action} admin account. Admin username: {username}")
        )
