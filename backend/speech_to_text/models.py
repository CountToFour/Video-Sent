from django.db import models
from downloader.models import Video


class Transcript(models.Model):
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='transcript')
    text = models.TextField()

    def __str__(self):
        return f'Transcript - {self.video.title}'