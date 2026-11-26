from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from app.accounts.permissions import IsAdminOrReadOnly
from app.orders.models import Kit
from app.orders.serializers import KitSerializer


class KitViewSet(viewsets.ModelViewSet):
    """
    Kits in the shared stock. Any logged-in user can list/retrieve;
    only admins can create, update or delete.

    To upload an image, send the request as multipart/form-data with the file in `image`.
    Plain JSON works for everything else.
    """

    queryset = Kit.objects.order_by("name", "variant_label", "id")
    serializer_class = KitSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def destroy(self, request, *args, **kwargs):
        # Kits referenced by order items are protected (on_delete=PROTECT).
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This kit is used in existing orders and cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
