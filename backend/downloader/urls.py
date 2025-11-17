from rest_framework.routers import DefaultRouter
from downloader.views import VideoViewSet

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    # ...
    *router.urls,
]
