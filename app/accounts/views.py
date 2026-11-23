from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from app.accounts.permissions import IsAdmin
from app.accounts.otp import issue_otp
from app.accounts.serializers import (
    DoctorSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    MeSerializer,
    ResetPasswordSerializer,
    VerifyOTPSerializer,
)

User = get_user_model()


class DoctorViewSet(viewsets.ModelViewSet):
    """Admin-only management of doctor accounts. Doctors then log in via /api/auth/token/."""

    queryset = User.objects.filter(role=User.Role.DOCTOR).prefetch_related("facilities").order_by("id")
    serializer_class = DoctorSerializer
    permission_classes = [IsAdmin]


@api_view(["GET"])
def me(request):
    """Return the logged-in user (role tells the frontend whether it's an admin or a doctor)."""
    return Response(MeSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """POST {"email", "password"} -> {"token", "user"}. Send the token as `Authorization: Token <token>`."""
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": MeSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    """POST {"email"} -> emails a 6-digit OTP if the account exists. Same response either way."""
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(email=serializer.validated_data["email"].lower(), is_active=True).first()
    if user is not None:
        issue_otp(user)
    # Don't reveal whether the email is registered.
    return Response({"detail": "If an account exists for this email, an OTP has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    """POST {"email", "otp"} -> 200 if the OTP is valid. Does not use up the OTP."""
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response({"detail": "OTP is valid."})


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """POST {"email", "otp", "new_password", "confirm_password"} -> sets the new password."""
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Password has been reset. Please log in with your new password."})
