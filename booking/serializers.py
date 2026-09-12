from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Booking, Court, Slot, Team, User


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "role", "is_active", "created_at"]
        read_only_fields = ["id", "role", "created_at"]


class TeamSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    team_name = serializers.CharField(required=False, allow_blank=True)
    owner_name = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=8)
    is_active = serializers.BooleanField(write_only=True, required=False)
    bookings_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "team_name",
            "owner_name",
            "user",
            "username",
            "email",
            "password",
            "is_active",
            "bookings_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "bookings_count"]

    def create(self, validated_data):
        username = validated_data.pop("username")
        email = validated_data.pop("email", "")
        password = validated_data.pop("password", None)
        is_active = validated_data.pop("is_active", True)
        if not password:
            raise serializers.ValidationError({"password": "Password is required when creating a team owner."})
        team_name = validated_data.pop("team_name", "") or username
        owner_name = validated_data.pop("owner_name", "") or username
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=User.Role.TEAM_OWNER,
            is_active=is_active,
        )
        return Team.objects.create(user=user, team_name=team_name, owner_name=owner_name, **validated_data)

    def update(self, instance, validated_data):
        user = instance.user
        username = validated_data.pop("username", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)
        is_active = validated_data.pop("is_active", None)
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if is_active is not None:
            user.is_active = is_active
        if password:
            user.set_password(password)
        user.save()
        return super().update(instance, validated_data)


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ["id", "court_number", "active"]


class SlotSerializer(serializers.ModelSerializer):
    court_number = serializers.IntegerField(source="court.court_number", read_only=True)
    booked = serializers.SerializerMethodField()
    is_my_booking = serializers.SerializerMethodField()
    booking = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = [
            "id",
            "date",
            "court",
            "court_number",
            "start_time",
            "end_time",
            "active",
            "created_at",
            "booked",
            "is_my_booking",
            "booking",
        ]
        read_only_fields = ["id", "created_at", "court_number", "booked", "is_my_booking", "booking"]

    def _active_booking(self, obj):
        return next((booking for booking in getattr(obj, "prefetched_active_bookings", []) if booking.status == Booking.Status.CONFIRMED), None)

    def get_booked(self, obj):
        return self._active_booking(obj) is not None

    def get_is_my_booking(self, obj):
        booking = self._active_booking(obj)
        request = self.context.get("request")
        return bool(booking and request and hasattr(request.user, "team") and booking.team_id == request.user.team.id)

    def get_booking(self, obj):
        request = self.context.get("request")
        booking = self._active_booking(obj)
        if not booking or not request or not request.user.is_admin_role:
            return None
        return BookingSerializer(booking, context=self.context).data


class BookingSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.team_name", read_only=True)
    owner_name = serializers.CharField(source="team.owner_name", read_only=True)
    date = serializers.DateField(source="slot.date", read_only=True)
    court_number = serializers.IntegerField(source="slot.court.court_number", read_only=True)
    start_time = serializers.TimeField(source="slot.start_time", read_only=True)
    end_time = serializers.TimeField(source="slot.end_time", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "team",
            "team_name",
            "owner_name",
            "slot",
            "date",
            "court_number",
            "start_time",
            "end_time",
            "status",
            "booked_at",
            "updated_at",
        ]
        read_only_fields = ["id", "booked_at", "updated_at", "team_name", "owner_name", "date", "court_number", "start_time", "end_time"]


class CreateBookingSerializer(serializers.Serializer):
    slot = serializers.PrimaryKeyRelatedField(queryset=Slot.objects.filter(active=True, court__active=True))

    def validate(self, attrs):
        request = self.context["request"]
        if not hasattr(request.user, "team"):
            raise serializers.ValidationError("Only team owners can book slots.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        slot = validated_data["slot"]
        team = request.user.team
        try:
            with transaction.atomic():
                locked_slot = Slot.objects.select_for_update().get(pk=slot.pk, active=True, court__active=True)
                active_bookings = Booking.objects.select_for_update().filter(
                    team=team,
                    status=Booking.Status.CONFIRMED,
                )
                if active_bookings.count() >= 2:
                    raise serializers.ValidationError({"detail": "Your team can book a maximum of 2 slots."})
                if active_bookings.filter(slot_date=locked_slot.date).exists():
                    raise serializers.ValidationError({"detail": "Your team can book only 1 slot per day."})
                booking = Booking.objects.create(
                    team=team,
                    slot=locked_slot,
                    created_by=request.user,
                    updated_by=request.user,
                )
                return booking
        except IntegrityError as exc:
            message = "This slot is no longer available or your team already booked a slot for this date."
            raise serializers.ValidationError({"detail": message}) from exc
