from django.db.models import Count, Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Booking, Court, Slot, Team
from .permissions import IsAdminRole, IsTeamOwner
from .serializers import (
    BookingSerializer,
    CourtSerializer,
    CreateBookingSerializer,
    LoginSerializer,
    SlotSerializer,
    TeamSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class CurrentUserView(APIView):
    def get(self, request):
        data = UserSerializer(request.user).data
        if hasattr(request.user, "team"):
            data["team"] = TeamSerializer(request.user.team).data
        return Response(data)


class AdminTeamViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = TeamSerializer

    def get_queryset(self):
        return Team.objects.select_related("user").annotate(
            bookings_count=Count("bookings", filter=Q(bookings__status=Booking.Status.CONFIRMED))
        ).order_by("team_name")


class AdminCourtViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = CourtSerializer

    def get_queryset(self):
        Court.objects.get_or_create(court_number=1, defaults={"active": True})
        return Court.objects.all()


class AdminSlotViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = SlotSerializer

    def get_queryset(self):
        active_bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).select_related("team", "slot__court")
        return Slot.objects.select_related("court").prefetch_related(
            Prefetch("bookings", queryset=active_bookings, to_attr="prefetched_active_bookings")
        )

    def destroy(self, request, *args, **kwargs):
        slot = self.get_object()
        if slot.bookings.filter(status=Booking.Status.CONFIRMED).exists():
            return Response(
                {"detail": "Cancel the confirmed booking before deleting this slot."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)


class AdminBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = BookingSerializer
    queryset = Booking.objects.select_related("team", "slot", "slot__court").all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.Status.CANCELLED
        booking.updated_by = request.user
        booking.save(update_fields=["status", "updated_by", "updated_at"])
        return Response(self.get_serializer(booking).data)


class OwnerSlotViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsTeamOwner]
    serializer_class = SlotSerializer

    def get_queryset(self):
        active_bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).select_related("team", "slot__court")
        return Slot.objects.filter(active=True, court__active=True).select_related("court").prefetch_related(
            Prefetch("bookings", queryset=active_bookings, to_attr="prefetched_active_bookings")
        )


class OwnerBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTeamOwner]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateBookingSerializer
        return BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(team=self.request.user.team).select_related("team", "slot", "slot__court")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingSerializer(booking, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.Status.CANCELLED
        booking.updated_by = request.user
        booking.save(update_fields=["status", "updated_by", "updated_at"])
        return Response(BookingSerializer(booking, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_summary(request):
    total_slots = Slot.objects.filter(active=True, court__active=True).count()
    booked_slots = Booking.objects.filter(status=Booking.Status.CONFIRMED).count()
    return Response(
        {
            "total_teams": Team.objects.count(),
            "total_slots": total_slots,
            "booked_slots": booked_slots,
            "available_slots": max(total_slots - booked_slots, 0),
            "teams_with_bookings": Team.objects.filter(bookings__status=Booking.Status.CONFIRMED).distinct().count(),
        }
    )


class OwnerSummaryView(APIView):
    permission_classes = [IsTeamOwner]

    def get(self, request):
        team = request.user.team
        bookings = Booking.objects.filter(team=team, status=Booking.Status.CONFIRMED).select_related("slot", "slot__court")
        return Response(
            {
                "team_name": team.team_name,
                "owner_name": team.owner_name,
                "total_bookings": bookings.count(),
                "booked_dates": list(bookings.values_list("slot__date", flat=True).distinct()),
            }
        )
