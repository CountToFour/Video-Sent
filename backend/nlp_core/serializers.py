from rest_framework import serializers
from .models import FeatureSentiment

class FeatureSentimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSentiment
        fields = '__all__'