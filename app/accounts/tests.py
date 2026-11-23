import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from app.accounts.choices import Role
from app.accounts.models import PasswordResetOTP
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
            {"email": "doc@example.com", "password": "Str0ng-pass-123"},
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
        payload = {"email": "admin@example.com", "password": "pass-12345", **overrides}
        return self.client.post(self.url, payload, format="json")

    def test_login_returns_token_and_user(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["token"])
        self.assertEqual(response.data["user"]["role"], Role.ADMIN)

    def test_email_is_case_insensitive(self):
        response = self.login(email="ADMIN@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_and_password_required(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("email", "password"):
            self.assertIn(field, response.data)

    def test_unknown_email_rejected(self):
        self.assertEqual(self.login(email="nobody@example.com").status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_password_rejected(self):
        self.assertEqual(self.login(password="nope").status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_rejected(self):
        self.admin.is_active = False
        self.admin.save()
        self.assertEqual(self.login().status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ForgotPasswordTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            email="doc@example.com", name="Dr Who", password="Old-pass-123", role=Role.DOCTOR
        )
        self.forgot_url = reverse("password-forgot")
        self.verify_url = reverse("password-verify-otp")
        self.reset_url = reverse("password-reset")

    def request_otp(self, email="doc@example.com"):
        response = self.client.post(self.forgot_url, {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1) if mail.outbox else None

    def reset(self, otp, new="New-pass-456", confirm=None, email="doc@example.com"):
        payload = {"email": email, "otp": otp, "new_password": new, "confirm_password": confirm or new}
        return self.client.post(self.reset_url, payload, format="json")

    def wrong(self, otp):
        return "000000" if otp != "000000" else "111111"

    def test_full_flow(self):
        otp = self.request_otp()
        self.assertEqual(mail.outbox[0].to, ["doc@example.com"])
        self.assertNotIn(otp, PasswordResetOTP.objects.get().code_hash)  # stored hashed

        verify = self.client.post(self.verify_url, {"email": "doc@example.com", "otp": otp}, format="json")
        self.assertEqual(verify.status_code, status.HTTP_200_OK)

        Token.objects.create(user=self.doctor)
        response = self.reset(otp)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.doctor.refresh_from_db()
        self.assertTrue(self.doctor.check_password("New-pass-456"))
        self.assertFalse(Token.objects.filter(user=self.doctor).exists())  # old sessions logged out

        login = self.client.post(
            reverse("api-token"),
            {"email": "doc@example.com", "password": "New-pass-456"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_unknown_email_same_response_no_email(self):
        response = self.client.post(self.forgot_url, {"email": "nobody@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_otp_cannot_be_reused(self):
        otp = self.request_otp()
        self.assertEqual(self.reset(otp).status_code, status.HTTP_200_OK)
        response = self.reset(otp, new="Another-pass-789")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)

    def test_wrong_otp_rejected(self):
        otp = self.request_otp()
        response = self.reset(self.wrong(otp))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)

    def test_expired_otp_rejected(self):
        otp = self.request_otp()
        PasswordResetOTP.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.reset(otp).status_code, status.HTTP_400_BAD_REQUEST)

    def test_locked_after_max_attempts(self):
        otp = self.request_otp()
        for _ in range(5):
            self.reset(self.wrong(otp))
        # Even the correct code is refused now.
        self.assertEqual(self.reset(otp).status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwords_must_match_and_do_not_use_attempt(self):
        otp = self.request_otp()
        response = self.reset(otp, new="New-pass-456", confirm="Different-789")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)
        self.assertEqual(PasswordResetOTP.objects.get().attempts, 0)

    def test_weak_password_rejected(self):
        otp = self.request_otp()
        response = self.reset(otp, new="123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_resend_cooldown(self):
        self.request_otp()
        self.request_otp()
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(PASSWORD_RESET_OTP_RESEND_COOLDOWN_SECONDS=0)
    def test_new_otp_replaces_old_one(self):
        old = self.request_otp()
        new = self.request_otp()
        self.assertEqual(len(mail.outbox), 2)
        if old != new:
            self.assertEqual(self.reset(old).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.reset(new).status_code, status.HTTP_200_OK)
