from django.test import TestCase
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
import whisper

from downloader.models import Video
from speech_to_text import services as stt_services


class TranscribeAudioToFileTests(TestCase):
    def setUp(self):
        # Tymczasowy katalog na audio i transkrypcje
        self.tmp_dir = TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

        self.base_path = Path(self.tmp_dir.name)
        self.audio_dir = self.base_path / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.transcripts_dir = self.base_path / "transcripts"
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

        # Podmieniamy katalog transkrypcji w module services
        self._orig_transcripts_dir = stt_services.TRANSCRIPTS_DIR
        stt_services.TRANSCRIPTS_DIR = self.transcripts_dir
        self.addCleanup(self._restore_transcripts_dir)

        # Mockujemy model whisper, żeby nie ładować prawdziwego modelu
        stt_services._model = MagicMock()
        self.mock_model = stt_services._model

    def _restore_transcripts_dir(self):
        stt_services.TRANSCRIPTS_DIR = self._orig_transcripts_dir

    def test_missing_audio_raises(self):
        missing_path = self.audio_dir / "missing.mp3"
        with self.assertRaises(RuntimeError) as ctx:
            stt_services.transcribe_audio_to_file(str(missing_path))

        msg = str(ctx.exception)
        self.assertIn("Błąd procesu transkrypcji: Plik audio nie istnieje", msg)

    def test_returns_existing_when_no_overwrite(self):
        audio_path = self.audio_dir / "file.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        transcript_path.write_text("existing transcript", encoding="utf-8")

        result = stt_services.transcribe_audio_to_file(str(audio_path), overwrite=False)

        self.assertEqual(Path(result), transcript_path.resolve())
        self.mock_model.transcribe.assert_not_called()

    def test_creates_transcript_and_calls_model(self):
        audio_path = self.audio_dir / "file2.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        # Ustawiamy wynik mocka
        self.mock_model.transcribe.return_value = {"text": " Hello world  "}

        result = stt_services.transcribe_audio_to_file(str(audio_path), overwrite=True)

        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        self.assertEqual(Path(result), transcript_path.resolve())
        self.assertTrue(transcript_path.exists())
        self.assertEqual(transcript_path.read_text(encoding="utf-8"), "Hello world")

        self.mock_model.transcribe.assert_called_once()
        called_path = self.mock_model.transcribe.call_args.kwargs.get("audio") or \
                      self.mock_model.transcribe.call_args.args[0]
        self.assertEqual(Path(called_path), audio_path)


    def test_wraps_whisper_generic_error(self):
        """
        Gdy _model.transcribe rzuci dowolny inny wyjątek,
        funkcja powinna rzucić RuntimeError z komunikatem
        'Błąd procesu transkrypcji: ...'.
        """
        audio_path = self.audio_dir / "file4.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        self.mock_model.transcribe.side_effect = Exception("GPU out of memory")

        with self.assertRaises(RuntimeError) as ctx:
            stt_services.transcribe_audio_to_file(str(audio_path), overwrite=True)

        msg = str(ctx.exception)
        self.assertIn("Błąd procesu transkrypcji: GPU out of memory", msg)

        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        self.assertFalse(transcript_path.exists())



class TranscribeVideoTests(TestCase):
    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

        self.base_path = Path(self.tmp_dir.name)
        self.audio_dir = self.base_path / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.transcripts_dir = self.base_path / "transcripts"
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

        # Podmieniamy katalog transkrypcji w module services
        self._orig_transcripts_dir = stt_services.TRANSCRIPTS_DIR
        stt_services.TRANSCRIPTS_DIR = self.transcripts_dir
        self.addCleanup(self._restore_transcripts_dir)

        # Mock Whisper
        stt_services._model = MagicMock()
        self.mock_model = stt_services._model

    def _restore_transcripts_dir(self):
        stt_services.TRANSCRIPTS_DIR = self._orig_transcripts_dir

    def _create_video_with_audio(self, filename: str = "audio.mp3") -> Video:
        audio_path = self.audio_dir / filename
        audio_path.write_text("dummy audio", encoding="utf-8")
        return Video.objects.create(
            url=f"https://example.com/{filename}",
            platform="other",
            audio_path=str(audio_path.resolve()),
        )

    @patch("speech_to_text.services.download_audio_with_ytdlp")
    def test_no_audio_path_download_fails_raises_value_error(self, mock_dl):
        """
        Dla braku audio_path funkcja próbuje pobrać audio;
        jeśli pobranie się nie uda, rzuca ValueError z odpowiednim komunikatem.
        """
        video = Video.objects.create(
            url="https://example.com/no-audio",
            platform="other",
            audio_path="",
        )
        mock_dl.side_effect = Exception("network error")

        with self.assertRaises(ValueError) as ctx:
            stt_services.transcribe_video(video)

        msg = str(ctx.exception)
        self.assertIn("Nie udało się pobrać brakującego audio", msg)

    @patch("speech_to_text.services.download_audio_with_ytdlp")
    def test_missing_audio_file_is_re_downloaded_successfully(self, mock_dl):
        """
        Jeśli video.audio_path wskazuje na plik, który NIE istnieje na dysku,
        transcribe_video powinno spróbować pobrać audio ponownie i kontynuować
        transkrypcję na nowej ścieżce.
        """
        # Tworzymy wideo ze ścieżką do nieistniejącego pliku
        missing_audio_path = self.audio_dir / "missing.mp3"
        video = Video.objects.create(
            url="https://example.com/missing",
            platform="other",
            audio_path=str(missing_audio_path),
        )

        # Symulujemy udane pobranie nowego pliku audio
        repaired_audio_path = self.audio_dir / "repaired.mp3"
        repaired_audio_path.write_text("new audio", encoding="utf-8")
        mock_dl.return_value = ("title", str(repaired_audio_path.resolve()))

        # Model Whisper zwraca jakiś tekst
        self.mock_model.transcribe.return_value = {"text": "Repaired text"}

        updated = stt_services.transcribe_video(video, force=False)

        # After self-healing, audio_path powinien być zaktualizowany
        video.refresh_from_db()
        self.assertEqual(video.audio_path, str(repaired_audio_path.resolve()))

        # Powinien powstać plik transkrypcji na bazie nowej ścieżki
        expected_transcript = self.transcripts_dir / f"{repaired_audio_path.stem}.txt"
        self.assertTrue(expected_transcript.exists())
        self.assertEqual(updated.transcript_path, str(expected_transcript.resolve()))

        # download_audio_with_ytdlp powinien zostać wywołany raz
        mock_dl.assert_called_once_with(video.url)
        self.mock_model.transcribe.assert_called_once()

    @patch("speech_to_text.services.download_audio_with_ytdlp")
    def test_missing_audio_file_repair_failure_raises_runtime_error(self, mock_dl):
        """
        Jeśli plik audio nie istnieje i próba ponownego pobrania kończy się błędem,
        transcribe_video powinno rzucić RuntimeError z odpowiednim komunikatem.
        """
        missing_audio_path = self.audio_dir / "missing2.mp3"
        video = Video.objects.create(
            url="https://example.com/missing2",
            platform="other",
            audio_path=str(missing_audio_path),
        )

        mock_dl.side_effect = Exception("network down")

        with self.assertRaises(RuntimeError) as ctx:
            stt_services.transcribe_video(video, force=False)

        msg = str(ctx.exception)
        self.assertIn("Nie udało się naprawić brakującego pliku audio: network down", msg)
        mock_dl.assert_called_once_with(video.url)

        # Upewniamy się, że transkrypcja nie została wykonana
        self.mock_model.transcribe.assert_not_called()

    def test_uses_existing_transcript_when_set(self):
        video = self._create_video_with_audio("a1.mp3")

        existing_transcript = self.transcripts_dir / "a1.txt"
        existing_transcript.write_text("existing", encoding="utf-8")

        video.transcript_path = str(existing_transcript.resolve())
        video.save()

        updated = stt_services.transcribe_video(video, force=False)

        self.assertEqual(updated.pk, video.pk)
        self.assertEqual(updated.transcript_path, str(existing_transcript.resolve()))
        self.mock_model.transcribe.assert_not_called()

    def test_sets_existing_transcript_when_field_empty(self):
        video = self._create_video_with_audio("a2.mp3")
        audio_path = Path(video.audio_path)
        expected_transcript = self.transcripts_dir / f"{audio_path.stem}.txt"
        expected_transcript.write_text("pre-existing", encoding="utf-8")

        self.assertFalse(video.transcript_path)

        updated = stt_services.transcribe_video(video, force=False)

        self.assertEqual(updated.transcript_path, str(expected_transcript.resolve()))
        # Odśwież z bazy, żeby upewnić się, że zapisano
        video.refresh_from_db()
        self.assertEqual(video.transcript_path, str(expected_transcript.resolve()))
        self.mock_model.transcribe.assert_not_called()

    def test_transcribes_when_no_transcript_exists(self):
        video = self._create_video_with_audio("a3.mp3")
        audio_path = Path(video.audio_path)

        # Upewniamy się, że nie ma transkryptu
        expected_transcript = self.transcripts_dir / f"{audio_path.stem}.txt"
        self.assertFalse(expected_transcript.exists())

        self.mock_model.transcribe.return_value = {"text": "Dummy text"}

        updated = stt_services.transcribe_video(video, force=False)

        self.assertTrue(expected_transcript.exists())
        self.assertEqual(updated.transcript_path, str(expected_transcript.resolve()))
        video.refresh_from_db()
        self.assertEqual(video.transcript_path, str(expected_transcript.resolve()))
        self.mock_model.transcribe.assert_called_once()

class WhisperRealIntegrationTest(TestCase):
    """
    Prawdziwy test integracyjny:
    - używa realnego modelu Whisper (whisper.load_model("base")),
    - korzysta z istniejącego pliku media/audio/fLeJJPxua3E.mp3,
    - zapisuje transkrypcję do media/transcripts/fLeJJPxua3E.txt.

    Uwaga: test jest wolny i wymaga zainstalowanego ffmpeg/ffprobe.
    """

    def setUp(self):
        self.base_media = Path("media")
        self.audio_dir = self.base_media / "audio"
        self.transcripts_dir = stt_services.TRANSCRIPTS_DIR

        self.audio_path = self.audio_dir / "fLeJJPxua3E.mp3"
        if not self.audio_path.exists():
            self.skipTest(f"Brak pliku audio {self.audio_path} – test integracyjny pominięty.")

        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_path = self.transcripts_dir / f"{self.audio_path.stem}.txt"

        # Sprzątamy potencjalny stary plik transkrypcji, żeby mieć czyste środowisko
        if self.transcript_path.exists():
            self.transcript_path.unlink()

        # Przywracamy prawdziwy model Whisper (na wypadek, gdy inne testy go zmockowały)
        stt_services._model = whisper.load_model("base")

        # Sprzątanie po teście
        self.addCleanup(self._cleanup_transcript_file)

    def _cleanup_transcript_file(self):
        if self.transcript_path.exists():
            self.transcript_path.unlink()

    def test_real_whisper_on_existing_audio(self):
        """
        Używa transcribe_audio_to_file z realnym Whisperem na pliku fLeJJPxua3E.mp3
        i sprawdza, że powstał niepusty plik transkrypcji.
        """
        result_path = stt_services.transcribe_audio_to_file(
            str(self.audio_path),
            overwrite=True,
        )

        # Ścieżka powinna wskazywać na media/transcripts/fLeJJPxua3E.txt
        self.assertEqual(Path(result_path), self.transcript_path.resolve())
        self.assertTrue(self.transcript_path.exists())

        content = self.transcript_path.read_text(encoding="utf-8").strip()
        # Zawartość nie powinna być pusta (Whisper coś zwrócił)
        self.assertNotEqual(content, "")
        # Opcjonalnie: można sprawdzić minimalną długość
        self.assertGreater(len(content), 10)