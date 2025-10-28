from django.db import models

class Platform(models.TextChoices):
    YOUTUBE = "youtube", "YouTube"
    TIKTOK = "tiktok", "TikTok"
    INSTAGRAM = "instagram", "Instagram"

class Video(models.Model):
    url = models.URLField(unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    title = models.CharField(max_length=255)
    local_path = models.FilePathField(path='media/videos', null=True, blank=True)

    def __str__(self):
        return f'{self.platform}: {self.title}'

