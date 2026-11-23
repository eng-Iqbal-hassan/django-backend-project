from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.accounts.choices import Role
from app.facilities.models import Facility

User = get_user_model()


class SuperuserTests(APITestCase):
    def test_createsuperuser_is_admin(self):
        admin = User.objects.create_superuser(email="root@example.com", name="Root", password="pass-12345")
        self.assertEqual(admin.role, Role.ADMIN)
        self.assertTrue(admin.is_admin)


class DoctorAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", name="Admin", password="pass-12345")
        self.facility = Facility.objects.create(facility_code="F001", facility_name="Cardiology")
        self.list_url = reverse("doctor-list")
        self.client.force_authenticate(self.admin)

    def create_doctor(self, **overrides):
        payload = {
            "email": "Doc@Example.com",
            "name": "Dr Who",
            "password": "Str0ng-pass-123",
            "facilities": [self.facility.pk],
            **overrides,
        }
        return self.client.post(self.list_url, payload, format="json")

    def test_admin_creates_doctor_then_doctor_logs_in(self):
        response = self.create_doctor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

        doctor = User.objects.get(email="doc@example.com")
        self.assertEqual(doctor.role, Role.DOCTOR)
        self.assertFalse(doctor.is_staff)
        self.assertEqual(list(doctor.facilities.all()), [self.facility])

        # Doctor logs in with the credentials the admin set.
        self.client.force_authenticate(None)
        login = self.client.post(
            reverse("api-token"),
            {"name": "Dr Who", "email": "doc@example.com", "password": "Str0ng-pass-123"},
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")

        me = self.client.get(reverse("me"))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["role"], Role.DOCTOR)
        self.assertEqual(me.data["facilities"], [self.facility.pk])

    def test_role_cannot_be_overridden(self):
        response = self.create_doctor(role=Role.ADMIN)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="doc@example.com").role, Role.DOCTOR)

    def test_password_required_on_create(self):
        response = self.create_doctor(password="")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_duplicate_email_rejected(self):
        self.create_doctor()
        response = self.create_doctor(email="doc@example.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_list_only_returns_doctors(self):
        self.create_doctor()
        response = self.client.get(self.list_url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], "doc@example.com")

    def test_update_password(self):
        doctor_id = self.create_doctor().data["id"]
        url = reverse("doctor-detail", args=[doctor_id])
        response = self.client.patch(url, {"password": "N3w-pass-4567"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(pk=doctor_id).check_password("N3w-pass-4567"))

    def test_doctor_cannot_manage_doctors(self):
        self.create_doctor()
        doctor = User.objects.get(email="doc@example.com")
        self.client.force_authenticate(doctor)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.create_doctor(email="other@example.com").status_code, status.HTTP_403_FORBIDDEN
        )

    def test_anonymous_cannot_access(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(reverse("me")).status_code, status.HTTP_401_UNAUTHORIZED)


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("api-token")
        self.admin = User.objects.create_superuser(email="admin@example.com", name="Admin User", password="pass-12345")

    def login(self, **overrides):
        payload = {"name": "Admin User", "email": "admin@example.com", "password": "pass-12345", **overrides}
        return self.client.post(self.url, payload, format="json")

    def test_login_returns_token_and_user(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["token"])
        self.assertEqual(response.data["user"]["role"], Role.ADMIN)

    def test_name_and_email_are_case_insensitive(self):
        response = self.login(name="  admin user ", email="ADMIN@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_all_three_fields_required(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("name", "email", "password"):
            self.assertIn(field, response.data)

    def test_wrong_name_rejected(self):
        self.assertEqual(self.login(name="Someone Else").status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_password_rejected(self):
        self.assertEqual(self.login(password="nope").status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_rejected(self):
        self.admin.is_active = False
        self.admin.save()
        self.assertEqual(self.login().status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
