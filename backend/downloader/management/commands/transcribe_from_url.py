from django.core.management.base import BaseCommand, CommandError

from downloader.services import get_or_create_video_with_audio
from speech_to_text.services import transcribe_video


class Command(BaseCommand):
    help = "Pobiera audio z URL i generuje transkrypcję. Aktualizuje model Video."

    def add_arguments(self, parser):
        parser.add_argument("url", type=str, help="URL filmu (YouTube/TikTok/Instagram)")

    def handle(self, *args, **options):
        url = options["url"]

        self.stdout.write(self.style.NOTICE(f"Przetwarzam URL: {url}"))

        try:
            video = get_or_create_video_with_audio(url)
            self.stdout.write(self.style.SUCCESS(f"Audio OK: {video.audio_path}"))

            video = transcribe_video(video)
            self.stdout.write(self.style.SUCCESS(
                f"Transkrypcja OK: {video.transcript_path}"
            ))
        except Exception as e:
            raise CommandError(str(e))
