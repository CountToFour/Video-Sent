from rest_framework.routers import DefaultRouter
from .views import FeatureSentimentViewSet

router = DefaultRouter()
router.register(r'sentiments', FeatureSentimentViewSet)

urlpatterns = router.urls