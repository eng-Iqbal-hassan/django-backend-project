from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.accounts.choices import Role
from app.facilities.models import Facility

User = get_user_model()


class FacilityAPITests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            email="doc@example.com", name="Doc", password="pass-12345", role=Role.DOCTOR
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", name="Admin", password="pass-12345", role=Role.ADMIN, is_staff=True
        )
        self.facility = Facility.objects.create(facility_code="F001", facility_name="General Hospital")
        self.list_url = reverse("facility-list")
        self.detail_url = reverse("facility-detail", args=[self.facility.pk])
        self.client.force_authenticate(self.doctor)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_authentication(self):
        self.client.force_authenticate(None)
        token = self.client.post(
            reverse("api-token"), {"email": "doc@example.com", "password": "pass-12345"}
        ).data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["facility_code"], "F001")

    def test_retrieve(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"id": self.facility.pk, "facility_code": "F001", "facility_name": "General Hospital", "users": []},
        )

    def test_retrieve_missing_returns_404(self):
        response = self.client.get(reverse("facility-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_doctor_cannot_write(self):
        payload = {"facility_code": "F009", "facility_name": "Nope"}
        self.assertEqual(self.client.post(self.list_url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.put(self.detail_url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.patch(self.detail_url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(self.detail_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Facility.objects.filter(facility_code="F009").exists())
        self.assertTrue(Facility.objects.filter(pk=self.facility.pk).exists())

    def test_doctor_can_read(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    # --- Writes below are admin-only (data is maintained via Postman). ---

    def test_create_with_doctor(self):
        self.client.force_authenticate(self.admin)
        payload = {"facility_code": "F002", "facility_name": "City Clinic", "users": [self.doctor.pk]}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        facility = Facility.objects.get(facility_code="F002")
        self.assertEqual(list(facility.users.all()), [self.doctor])

    def test_create_rejects_non_doctor_user(self):
        self.client.force_authenticate(self.admin)
        payload = {"facility_code": "F003", "facility_name": "Bad Link", "users": [self.admin.pk]}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("users", response.data)
        self.assertFalse(Facility.objects.filter(facility_code="F003").exists())

    def test_create_rejects_duplicate_code(self):
        self.client.force_authenticate(self.admin)
        payload = {"facility_code": "F001", "facility_name": "Duplicate"}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("facility_code", response.data)

    def test_create_requires_fields(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("facility_code", response.data)
        self.assertIn("facility_name", response.data)

    def test_update(self):
        self.client.force_authenticate(self.admin)
        payload = {"facility_code": "F001", "facility_name": "Renamed Hospital", "users": [self.doctor.pk]}
        response = self.client.put(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.facility.refresh_from_db()
        self.assertEqual(self.facility.facility_name, "Renamed Hospital")
        self.assertEqual(list(self.facility.users.all()), [self.doctor])

    def test_partial_update(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.detail_url, {"facility_name": "Patched"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.facility.refresh_from_db()
        self.assertEqual(self.facility.facility_name, "Patched")
        self.assertEqual(self.facility.facility_code, "F001")

    def test_destroy(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Facility.objects.filter(pk=self.facility.pk).exists())
