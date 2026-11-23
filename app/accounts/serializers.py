from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

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
    """Login requires name, email and password; all three must match the same active user."""

    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].lower(),
            password=attrs["password"],
        )
        # Same message for every failure so we don't reveal which field was wrong.
        if user is None or user.name.strip().casefold() != attrs["name"].strip().casefold():
            raise serializers.ValidationError("Invalid name, email or password.", code="authorization")
        attrs["user"] = user
        return attrs
