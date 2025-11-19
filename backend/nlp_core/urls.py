from rest_framework.routers import DefaultRouter
from .views import FeatureSentimentViewSet
from django.urls import path
from .views import AnalyzeView


router = DefaultRouter()
router.register(r'sentiments', FeatureSentimentViewSet)

urlpatterns = router.urls + [
    path('analyze/', AnalyzeView.as_view(), name='nlp-analyze'),
]
