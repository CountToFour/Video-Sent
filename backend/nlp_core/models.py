from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from speech_to_text.models import Transcript

class SentimentLabel(models.TextChoices):
    NEGATIVE = "NEGATIVE", "Negative"
    NEUTRAL = "NEUTRAL", "Neutral"
    POSITIVE = "POSITIVE", "Positive"
    EXCELLENT = "EXCELLENT", "Excellent"

class FeatureSentiment(models.Model):
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name='feature_sentiments')
    feature = models.CharField(max_length=50)
    sentiment = models.CharField(max_length=20, choices=SentimentLabel.choices)
    score = models.DecimalField(default=0.00, max_digits=3, decimal_places=2, validators=[
        MinValueValidator(0.00),
        MaxValueValidator(1.00)
    ])
    summary = models.TextField(max_length=255)

