from django.urls import path
from rest_framework.routers import DefaultRouter

from app.accounts.views import DoctorViewSet, forgot_password, login, me, reset_password, verify_otp

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")

urlpatterns = [
    path("auth/token/", login, name="api-token"),
    path("auth/me/", me, name="me"),
    path("auth/password/forgot/", forgot_password, name="password-forgot"),
    path("auth/password/verify-otp/", verify_otp, name="password-verify-otp"),
    path("auth/password/reset/", reset_password, name="password-reset"),
] + router.urls
