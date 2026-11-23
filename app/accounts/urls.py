from django.urls import path
from rest_framework.routers import DefaultRouter

from app.accounts.views import DoctorViewSet, login, me

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")

urlpatterns = [
    path("auth/token/", login, name="api-token"),
    path("auth/me/", me, name="me"),
] + router.urls
