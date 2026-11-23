from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from app.accounts.permissions import IsAdmin
from app.accounts.serializers import DoctorSerializer, LoginSerializer, MeSerializer

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
    """POST {"name", "email", "password"} -> {"token", "user"}. Send the token as `Authorization: Token <token>`."""
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": MeSerializer(user).data})
