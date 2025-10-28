from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from downloader.models import Video

class SentimentLabel(models.TextChoices):
    NEGATIVE = "NEGATIVE", "Negative"
    NEUTRAL = "NEUTRAL", "Neutral"
    POSITIVE = "POSITIVE", "Positive"
    EXCELLENT = "EXCELLENT", "Excellent"

class FeatureSentiment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='feature_sentiments')
    feature = models.CharField(max_length=50)
    sentiment = models.CharField(max_length=20, choices=SentimentLabel.choices)
    score = models.FloatField(
        default=0.0,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ]
    )
    summary = models.TextField(max_length=255)

