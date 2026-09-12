from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Booking, Court, Slot, Team, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("KPL 7.0", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_active", "is_staff")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("team_name", "owner_name", "user", "created_at")
    search_fields = ("team_name", "owner_name", "user__username")


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("court_number", "active")


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("date", "court", "start_time", "end_time", "active")
    list_filter = ("date", "court", "active")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("team", "slot", "status", "booked_at")
    list_filter = ("status", "slot__date")
