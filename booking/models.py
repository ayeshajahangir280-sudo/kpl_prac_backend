from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEAM_OWNER = "TEAM_OWNER", "Team owner"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TEAM_OWNER)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser


class Team(models.Model):
    team_name = models.CharField(max_length=120)
    owner_name = models.CharField(max_length=120)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.team_name


class Court(models.Model):
    court_number = models.PositiveIntegerField(unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["court_number"]

    def __str__(self):
        return f"Court {self.court_number}"


class Slot(models.Model):
    date = models.DateField()
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name="slots")
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "court__court_number", "start_time"]
        constraints = [
            models.UniqueConstraint(fields=["date", "court", "start_time", "end_time"], name="unique_slot_time_per_court")
        ]

    def __str__(self):
        return f"{self.date} {self.court} {self.start_time}-{self.end_time}"


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="bookings")
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, related_name="bookings")
    slot_date = models.DateField(editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    booked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_bookings")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_bookings")

    class Meta:
        ordering = ["-booked_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["slot"],
                condition=Q(status="CONFIRMED"),
                name="unique_active_booking_per_slot",
            ),
            models.UniqueConstraint(
                fields=["team", "slot_date"],
                condition=Q(status="CONFIRMED"),
                name="unique_active_booking_per_team_date",
            ),
        ]

    def save(self, *args, **kwargs):
        self.slot_date = self.slot.date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.team} - {self.slot}"
