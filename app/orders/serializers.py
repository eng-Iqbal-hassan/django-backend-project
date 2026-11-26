from rest_framework import serializers

from app.orders.models import Kit

KIT_IMAGE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


class KitSerializer(serializers.ModelSerializer):
    # Returned as an absolute URL when the request is in the serializer context (viewsets pass it).
    # Send it as multipart/form-data to upload; send an empty value to remove the image.
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Kit
        fields = [
            "id",
            "name",
            "variant_label",
            "image",
            "stock_quantity",
            "ice_packs_per_kit",
            "fedex_packs_per_line",
            "requisition_per_kit",
        ]

    def validate_image(self, image):
        if image and image.size > KIT_IMAGE_MAX_BYTES:
            raise serializers.ValidationError("Image must be 5 MB or smaller.")
        return image
