import io
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from app.accounts.choices import Role
from app.facilities.models import Facility
from app.orders.models import Kit, Order, OrderItem

User = get_user_model()

TEST_MEDIA_ROOT = tempfile.mkdtemp()


def make_image(name="kit.png", fmt="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class KitAPITests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.doctor = User.objects.create_user(
            email="doc@example.com", name="Doc", password="pass-12345", role=Role.DOCTOR
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", name="Admin", password="pass-12345", role=Role.ADMIN, is_staff=True
        )
        self.kit = Kit.objects.create(name="Blood Kit", variant_label="Small", stock_quantity=10)
        self.list_url = reverse("kit-list")
        self.detail_url = reverse("kit-detail", args=[self.kit.pk])
        self.client.force_authenticate(self.doctor)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Blood Kit")
        self.assertIsNone(response.data["results"][0]["image"])

    def test_retrieve(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock_quantity"], 10)

    def test_doctor_cannot_write(self):
        payload = {"name": "Nope"}
        self.assertEqual(self.client.post(self.list_url, payload).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.patch(self.detail_url, payload).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(self.detail_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Kit.objects.filter(name="Nope").exists())

    # --- Admin writes ---

    def test_create_with_image_returns_absolute_url(self):
        self.client.force_authenticate(self.admin)
        payload = {"name": "Urine Kit", "stock_quantity": 5, "image": make_image()}
        response = self.client.post(self.list_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["image"].startswith("http://testserver/media/kits/"))
        kit = Kit.objects.get(name="Urine Kit")
        self.assertTrue(kit.image.name.startswith("kits/"))

    def test_create_with_json_and_no_image(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.list_url, {"name": "Swab Kit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["image"])

    def test_create_requires_name(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_rejects_non_image_file(self):
        self.client.force_authenticate(self.admin)
        bad = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
        response = self.client.post(self.list_url, {"name": "Bad", "image": bad}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    @mock.patch("app.orders.serializers.KIT_IMAGE_MAX_BYTES", 10)
    def test_rejects_oversized_image(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.detail_url, {"image": make_image()}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    def test_patch_uploads_image(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.detail_url, {"image": make_image("new.jpg", "JPEG")}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.kit.refresh_from_db()
        self.assertTrue(self.kit.image.name.startswith("kits/new"))
        self.assertEqual(self.kit.name, "Blood Kit")

    def test_patch_without_image_keeps_existing_image(self):
        self.client.force_authenticate(self.admin)
        self.client.patch(self.detail_url, {"image": make_image()}, format="multipart")
        response = self.client.patch(self.detail_url, {"stock_quantity": 3}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.kit.refresh_from_db()
        self.assertEqual(self.kit.stock_quantity, 3)
        self.assertTrue(self.kit.image)

    def test_patch_null_removes_image(self):
        self.client.force_authenticate(self.admin)
        self.client.patch(self.detail_url, {"image": make_image()}, format="multipart")
        response = self.client.patch(self.detail_url, {"image": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.kit.refresh_from_db()
        self.assertFalse(self.kit.image)

    def test_destroy(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Kit.objects.filter(pk=self.kit.pk).exists())

    def test_destroy_kit_in_order_returns_409(self):
        facility = Facility.objects.create(facility_code="F001", facility_name="General Hospital")
        order = Order.objects.create(facility=facility, placed_by=self.doctor)
        OrderItem.objects.create(order=order, kit=self.kit, quantity=1)
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Kit.objects.filter(pk=self.kit.pk).exists())
