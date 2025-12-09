import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from downloader.models import Video, Platform
from downloader.services import AUDIO_DIR
from downloader.services import detect_platform, get_or_create_video_with_audio
from downloader.services import download_audio_with_ytdlp


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

        raw = b"".join(response.streaming_content).decode("utf-8").strip().splitlines()
        last_line = raw[-1]
        payload = json.loads(last_line)

        self.assertEqual(payload.get("type"), "complete")
        data = payload.get("data", {})
        self.assertIn("nlp_results", data)
        self.assertIn("summary", data["nlp_results"]["user_summary"])

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

class DownloadAudioWithYtDlpTest(TestCase):

    @patch("downloader.services.yt_dlp.YoutubeDL")
    def test_download_uses_direct_mp3_file(self, mock_ytdl):
        """Gdy yt-dlp zwraca ID i plik mp3 istnieje — test podstawowej ścieżki."""

        # 🔹 przygotowanie fejkowego MP3
        fake_id = "abc123"
        fake_mp3_path = AUDIO_DIR / f"{fake_id}.mp3"
        fake_mp3_path.write_text("dummy")

        # 🔹 mock yt-dlp obiektu
        fake_info = {"id": fake_id, "title": "Test Video"}

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = fake_info

        mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance

        # 🔹 wywołanie
        title, path = download_audio_with_ytdlp("https://youtube.com/video")

        # 🔹 asercje
        self.assertEqual(title, "Test Video")
        self.assertEqual(path, str(fake_mp3_path.resolve()))

        # sprzątanie
        fake_mp3_path.unlink()


    @patch("downloader.services.yt_dlp.YoutubeDL")
    def test_download_uses_fallback_filename(self, mock_ytdl):
        """Gdy mp3 nie istnieje — sprawdzamy fallback przez prepare_filename()."""

        fake_id = "xyz123"

        fake_info = {"id": fake_id, "title": "Fallback Title"}

        # 🔹 mock YoutubeDL() context manager
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = fake_info
        mock_ydl_instance.prepare_filename.return_value = str(AUDIO_DIR / "fallback.mp3")

        mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance

        # 🔹 generujemy plik fallback
        fallback_file = AUDIO_DIR / "fallback.mp3"
        fallback_file.write_text("dummy data")

        title, path = download_audio_with_ytdlp("https://youtube.com/video")

        self.assertEqual(title, "Fallback Title")
        self.assertEqual(path, str(fallback_file.resolve()))

        fallback_file.unlink()


    @patch("downloader.services.yt_dlp.YoutubeDL")
    def test_download_fails_when_no_files_exist(self, mock_ytdl):
        """Sprawdzamy wyjątek, gdy yt-dlp nie stworzy żadnego pliku."""

        fake_id = "z99"
        fake_info = {"id": fake_id, "title": None}

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = fake_info
        mock_ydl_instance.prepare_filename.return_value = str(AUDIO_DIR / "nonexistent.mp3")

        mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance

        with self.assertRaises(FileNotFoundError):
            download_audio_with_ytdlp("https://youtube.com/video")

class VideoFromUrlStreamingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("video-from-url")

    @patch("downloader.views.summarize_nlp_results", return_value="summary text")
    @patch("downloader.views.nlp_services.save_results_for_video")
    @patch("downloader.views.nlp_services.analyze_text", return_value={"overall": {"label": "POSITIVE"}})
    @patch("downloader.views.transcribe_video")
    @patch("downloader.views.get_or_create_video_with_audio")
    def test_event_stream_success_flow(
            self, mock_get_or_create, mock_transcribe, mock_analyze, mock_save, mock_summary
    ):
        # 🔹 przygotuj fejkowy Video z istniejącą transkrypcją
        tmp_transcript_path = os.path.join(tempfile.gettempdir(), "stream_test_transcript.txt")
        with open(tmp_transcript_path, "w", encoding="utf-8") as f:
            f.write("fake transcript content")

        video = Video.objects.create(
            url="https://youtube.com/x",
            title="T",
            platform=Platform.YOUTUBE,
            audio_path=os.path.join(tempfile.gettempdir(), "audio.mp3"),
            transcript_path=tmp_transcript_path,
        )

        mock_get_or_create.return_value = video
        mock_transcribe.return_value = video

        # 🔹 wywołanie endpointu
        response = self.client.post(self.url, {"url": video.url}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/x-ndjson")

        # 🔹 odczyt strumienia
        raw_lines = b"".join(response.streaming_content).decode("utf-8").strip().splitlines()
        self.assertGreaterEqual(len(raw_lines), 5)  # kilka eventów progress + complete

        # sparsuj wszystkie linie
        events = [json.loads(line) for line in raw_lines]

        # 1) pierwsze eventy typu "progress"
        types = [e["type"] for e in events]
        self.assertIn("progress", types)
        self.assertIn("complete", types)

        # sprawdź konkretny komunikat inicjalizacji
        first = events[0]
        self.assertEqual(first["type"], "progress")
        self.assertEqual(first["message"], "Inicjalizacja...")
        self.assertEqual(first["progress"], 5)

        # 2) ostatni event powinien być typu "complete" z danymi
        last = events[-1]
        self.assertEqual(last["type"], "complete")
        self.assertIn("data", last)

        data = last["data"]
        self.assertIn("nlp_results", data)
        self.assertIn("user_summary", data["nlp_results"])
        self.assertEqual(data["nlp_results"]["user_summary"], "summary text")

        # 3) upewnijmy się, że pipeline został uruchomiony
        mock_get_or_create.assert_called_once()
        mock_transcribe.assert_called_once_with(video)
        mock_analyze.assert_called_once()
        mock_save.assert_called_once()
        mock_summary.assert_called_once()
