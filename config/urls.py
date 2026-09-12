from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from booking.views import (
    AdminBookingViewSet,
    AdminCourtViewSet,
    AdminSlotViewSet,
    AdminTeamViewSet,
    CurrentUserView,
    LoginView,
    OwnerBookingViewSet,
    OwnerSlotViewSet,
    OwnerSummaryView,
    admin_summary,
)

router = DefaultRouter()
router.register("admin/teams", AdminTeamViewSet, basename="admin-teams")
router.register("admin/courts", AdminCourtViewSet, basename="admin-courts")
router.register("admin/slots", AdminSlotViewSet, basename="admin-slots")
router.register("admin/bookings", AdminBookingViewSet, basename="admin-bookings")
router.register("owner/slots", OwnerSlotViewSet, basename="owner-slots")
router.register("owner/bookings", OwnerBookingViewSet, basename="owner-bookings")

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", CurrentUserView.as_view(), name="current_user"),
    path("api/admin/summary/", admin_summary, name="admin_summary"),
    path("api/owner/summary/", OwnerSummaryView.as_view(), name="owner_summary"),
    path("api/", include(router.urls)),
]
