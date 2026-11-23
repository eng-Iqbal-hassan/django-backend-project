from rest_framework.routers import DefaultRouter

from app.facilities.views import FacilityViewSet

router = DefaultRouter()
router.register("facilities", FacilityViewSet, basename="facility")

urlpatterns = router.urls
