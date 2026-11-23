from rest_framework import viewsets

from app.facilities.models import Facility
from app.accounts.permissions import IsAdminOrReadOnly
from app.facilities.serializers import FacilitySerializer


class FacilityViewSet(viewsets.ModelViewSet):
    """
    Facilities are reference data maintained by admins (e.g. via Postman).
    The frontend only uses list (GET /api/facilities/) and retrieve (GET /api/facilities/<id>/);
    create/update/delete are restricted to admins.
    """

    # Ordered so pagination is stable; prefetch avoids one query per facility for `users`.
    queryset = Facility.objects.prefetch_related("users").order_by("id")
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminOrReadOnly]
