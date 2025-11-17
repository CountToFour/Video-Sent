from django.db import models

class Platform(models.TextChoices):
    YOUTUBE = "youtube", "YouTube"
    TIKTOK = "tiktok", "TikTok"
    INSTAGRAM = "instagram", "Instagram"
    OTHER = "other", "Other"

class Video(models.Model):
    url = models.URLField(unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices, default=Platform.OTHER)
    title = models.CharField(max_length=255, blank=True)

    # Opcjonalnie: plik wideo, jeśli kiedyś będzie potrzebny
    local_path = models.FilePathField(
        path='media/videos', null=True, blank=True
    )

    # NOWE: ścieżka do wyodrębnionego audio
    audio_path = models.FilePathField(
        path='media/audio', null=True, blank=True
    )

    # NOWE: ścieżka do pliku z transkrypcją
    transcript_path = models.FilePathField(
        path='media/transcripts', null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


    def __str__(self):
        return f'{self.platform}: {self.title or self.url}'
