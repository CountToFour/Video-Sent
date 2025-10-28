from rest_framework import viewsets
from .models import FeatureSentiment
from .serializers import FeatureSentimentSerializer


class FeatureSentimentViewSet(viewsets.ModelViewSet):
    queryset = FeatureSentiment.objects.all()
    serializer_class = FeatureSentimentSerializer