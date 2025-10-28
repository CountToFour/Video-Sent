from rest_framework import serializers
from .models import FeatureSentiment

class FeatureSentimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSentiment
        field = '__all__'