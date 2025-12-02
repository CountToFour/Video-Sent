import os
import tempfile
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from downloader.models import Video, Platform
from downloader.services import detect_platform, get_or_create_video_with_audio


# ---------------------------------------------------------
#  TESTY MODELI
# ---------------------------------------------------------

class VideoModelTest(TestCase):

    def test_video_str(self):
        video = Video.objects.create(
            url="https://youtube.com/watch?v=test",
            platform=Platform.YOUTUBE,
            title="Test Title"
        )
        self.assertEqual(str(video), "youtube: Test Title")

    def test_video_str_no_title(self):
        video = Video.objects.create(
            url="https://example.com",
            platform=Platform.OTHER
        )
        self.assertEqual(str(video), f"other: {video.url}")


# ---------------------------------------------------------
#  TESTY SERWISÓW
# ---------------------------------------------------------

class DetectPlatformTest(TestCase):

    def test_detect_youtube(self):
        self.assertEqual(
            detect_platform("https://youtube.com/watch?v=abc"),
            Platform.YOUTUBE
        )

    def test_detect_tiktok(self):
        self.assertEqual(
            detect_platform("https://tiktok.com/x"),
            Platform.TIKTOK
        )

    def test_detect_instagram(self):
        self.assertEqual(
            detect_platform("https://instagram.com/reel/x"),
            Platform.INSTAGRAM
        )

    def test_detect_other(self):
        self.assertEqual(
            detect_platform("https://example.com"),
            Platform.OTHER
        )


class GetOrCreateVideoWithAudioTest(TestCase):

    @patch("downloader.services.download_audio_with_ytdlp")
    def test_creates_new_video_and_downloads_audio(self, mock_dl):
        mock_dl.return_value = ("Test Title", "/tmp/audio.mp3")
        url = "https://youtube.com/watch?v=123"

        video = get_or_create_video_with_audio(url)

        self.assertEqual(video.url, url)
        self.assertEqual(video.title, "Test Title")
        self.assertEqual(video.audio_path, "/tmp/audio.mp3")
        self.assertEqual(video.platform, Platform.YOUTUBE)
        self.assertIsNotNone(video.id)

    @patch("downloader.services.download_audio_with_ytdlp")
    def test_existing_video_does_not_redownload_audio(self, mock_dl):
        url = "https://youtube.com/watch?v=123"
        video = Video.objects.create(
            url=url,
            audio_path="/tmp/existing.mp3",
            platform=Platform.YOUTUBE
        )

        result = get_or_create_video_with_audio(url)

        mock_dl.assert_not_called()
        self.assertEqual(result.id, video.id)
        self.assertEqual(result.audio_path, "/tmp/existing.mp3")


# ---------------------------------------------------------
#  TESTY WIDOKÓW / API
# ---------------------------------------------------------

class VideoViewSetFromUrlTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("video-from-url")  # Django DRF action

    @patch("downloader.views.summarize_nlp_results", return_value="summary")
    @patch("downloader.views.nlp_services.save_results_for_video")
    @patch("downloader.views.nlp_services.analyze_text", return_value={"sentiment": "ok"})
    @patch("downloader.views.transcribe_video")
    @patch("downloader.views.get_or_create_video_with_audio")
    def test_from_url_success(
        self, mock_get, mock_transcribe, mock_analyze, mock_save, mock_summary
    ):
        tmp_transcript_path = os.path.join(tempfile.gettempdir(), "transcript.txt")

        video = Video.objects.create(
            url="https://youtube.com/x",
            transcript_path=tmp_transcript_path,
            title="T",
            platform=Platform.YOUTUBE,
            audio_path=os.path.join(tempfile.gettempdir(), "audio.mp3")
        )

        # symulujemy zapis transkrypcji
        with open(tmp_transcript_path, "w", encoding="utf-8") as f:
            f.write("test content")

        mock_get.return_value = video
        mock_transcribe.return_value = video

        response = self.client.post(self.url, {"url": video.url}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("nlp_results", response.data)
        self.assertIn("summary", response.data["nlp_results"]["user_summary"])

    def test_from_url_missing_body(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)


class VideoTranscriptTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_transcript_not_found(self):
        video = Video.objects.create(
            url="https://x.com",
            platform=Platform.OTHER,
            transcript_path=None
        )
        url = reverse("video-transcript", args=[video.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_transcript_success(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        tmp_file.write("TEST CONTENT".encode("utf-8"))
        tmp_file.close()

        video = Video.objects.create(
            url="https://x.com",
            platform=Platform.OTHER,
            transcript_path=tmp_file.name
        )

        url = reverse("video-transcript", args=[video.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["transcript"], "TEST CONTENT")
