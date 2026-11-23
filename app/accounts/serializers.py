from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from app.accounts.otp import InvalidOTP, check_otp

from app.facilities.models import Facility

User = get_user_model()


class DoctorSerializer(serializers.ModelSerializer):
    """Admin-facing serializer: creates/updates users that always have the DOCTOR role."""

    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})
    facilities = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), many=True, required=False
    )

    class Meta:
        model = User
        fields = ["id", "email", "name", "password", "is_active", "facilities"]

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        # Password is required when creating, optional when updating.
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "This field is required."})
        if attrs.get("password"):
            validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        facilities = validated_data.pop("facilities", [])
        doctor = User.objects.create_user(role=User.Role.DOCTOR, **validated_data)
        doctor.facilities.set(facilities)
        return doctor

    def update(self, instance, validated_data):
        facilities = validated_data.pop("facilities", None)
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        if facilities is not None:
            instance.facilities.set(facilities)
        return instance


class MeSerializer(serializers.ModelSerializer):
    """The logged-in user's own profile (used by the frontend after login)."""

    facilities = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "facilities"]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Login with email and password (the password is set by the admin, or by the user via forgot-password)."""

    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].lower(),
            password=attrs["password"],
        )
        # Same message for every failure so we don't reveal which field was wrong.
        if user is None:
            raise serializers.ValidationError("Invalid email or password.", code="authorization")
        attrs["user"] = user
        return attrs


def _active_user_by_email(email):
    return User.objects.filter(email=email.lower(), is_active=True).first()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.RegexField(r"^\d{6}$", error_messages={"invalid": "OTP must be 6 digits."})

    def validate(self, attrs):
        user = _active_user_by_email(attrs["email"])
        try:
            attrs["otp_record"] = check_otp(user, attrs["otp"])
        except InvalidOTP as exc:
            raise serializers.ValidationError({"otp": str(exc)})
        attrs["user"] = user
        return attrs


class ResetPasswordSerializer(VerifyOTPSerializer):
    new_password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)
    confirm_password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)

    def validate(self, attrs):
        # Check the passwords first so a typo doesn't use up an OTP attempt.
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        attrs = super().validate(attrs)
        try:
            validate_password(attrs["new_password"], user=attrs["user"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        return attrs

    @transaction.atomic
    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        now = timezone.now()
        user.password_reset_otps.filter(used_at__isnull=True).update(used_at=now)
        # Log out everywhere: existing tokens stop working after a reset.
        Token.objects.filter(user=user).delete()
        return user
