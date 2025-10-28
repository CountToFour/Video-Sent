from rest_framework.routers import DefaultRouter

from .views import TranscriptViewSet

router = DefaultRouter()
router.register(r'transcript', TranscriptViewSet)

urlpatterns = router.urls