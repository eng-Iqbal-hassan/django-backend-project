from rest_framework.routers import DefaultRouter

from app.orders.views import KitViewSet

router = DefaultRouter()
router.register("kits", KitViewSet, basename="kit")

urlpatterns = router.urls
