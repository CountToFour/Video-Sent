from django.test import TestCase
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock
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

    def test_transcribe_audio_to_file_raises_if_audio_missing(self):
        missing_path = self.audio_dir / "missing.mp3"
        with self.assertRaises(FileNotFoundError):
            stt_services.transcribe_audio_to_file(str(missing_path))

    def test_transcribe_audio_to_file_returns_existing_when_not_overwrite(self):
        audio_path = self.audio_dir / "file.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        transcript_path.write_text("existing transcript", encoding="utf-8")

        result = stt_services.transcribe_audio_to_file(str(audio_path), overwrite=False)

        self.assertEqual(Path(result), transcript_path.resolve())
        # Nie powinniśmy w ogóle wołać transcribe na modelu
        self.mock_model.transcribe.assert_not_called()

    def test_transcribe_audio_to_file_creates_transcript_and_calls_model(self):
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

    def test_transcribe_video_raises_when_no_audio_path(self):
        video = Video.objects.create(
            url="https://example.com/no-audio",
            platform="other",
            audio_path="",
        )
        with self.assertRaises(ValueError):
            stt_services.transcribe_video(video)

    def test_transcribe_video_returns_existing_when_transcript_path_and_file_exists(self):
        video = self._create_video_with_audio("a1.mp3")

        existing_transcript = self.transcripts_dir / "a1.txt"
        existing_transcript.write_text("existing", encoding="utf-8")

        video.transcript_path = str(existing_transcript.resolve())
        video.save()

        updated = stt_services.transcribe_video(video, force=False)

        self.assertEqual(updated.pk, video.pk)
        self.assertEqual(updated.transcript_path, str(existing_transcript.resolve()))
        self.mock_model.transcribe.assert_not_called()

    def test_transcribe_video_sets_transcript_if_expected_exists_and_field_empty(self):
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

    def test_transcribe_video_calls_transcribe_when_no_transcript_and_not_exists(self):
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

    def test_transcribe_video_force_overwrites_existing_transcript(self):
        video = self._create_video_with_audio("a4.mp3")
        audio_path = Path(video.audio_path)
        existing_transcript = self.transcripts_dir / f"{audio_path.stem}.txt"
        existing_transcript.write_text("old text", encoding="utf-8")

        video.transcript_path = str(existing_transcript.resolve())
        video.save()

        self.mock_model.transcribe.return_value = {"text": "new text"}

        updated = stt_services.transcribe_video(video, force=True)

        self.assertEqual(
            existing_transcript.read_text(encoding="utf-8"),
            "new text",
        )
        self.assertEqual(updated.transcript_path, str(existing_transcript.resolve()))
        self.mock_model.transcribe.assert_called_once()

class SpeechToTextIntegrationTests(TestCase):
    """
    Testy integracyjne korzystające z prawdziwego pliku audio w media/audio
    oraz rzeczywistego katalogu media/transcripts.
    Model Whisper jest nadal mockowany, żeby test był szybki i powtarzalny.
    """

    def setUp(self):
        # Prawdziwe katalogi używane w aplikacji
        self.base_media = Path("media")
        self.audio_dir = self.base_media / "audio"
        self.transcripts_dir = stt_services.TRANSCRIPTS_DIR

        # Plik audio, który już istnieje w projekcie
        self.audio_path = self.audio_dir / "fLeJJPxua3E.mp3"

        if not self.audio_path.exists():
            self.skipTest(f"Brak pliku audio {self.audio_path} – test integracyjny pominięty.")

        # Oczekiwany plik transkrypcji
        self.transcript_path = self.transcripts_dir / f"{self.audio_path.stem}.txt"

        # Upewniamy się, że katalog na transkrypcje istnieje
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

        # Sprzątamy potencjalne stare transkrypcje przed testem
        if self.transcript_path.exists():
            self.transcript_path.unlink()

        # Mock Whisper także tutaj – integrujemy z realnym FS i DB, nie z modelem
        stt_services._model = MagicMock()
        self.mock_model = stt_services._model

        # Sprzątanie po teście: usuń plik transkrypcji, jeśli powstał
        self.addCleanup(self._cleanup_transcript_file)

    def _cleanup_transcript_file(self):
        if self.transcript_path.exists():
            self.transcript_path.unlink()

    def test_transcribe_audio_to_file_with_real_audio_creates_transcript_in_media_dir(self):
        """
        Używa istniejącego pliku audio z media/audio i sprawdza,
        czy transcribe_audio_to_file tworzy plik .txt w media/transcripts
        oraz czy zawiera on treść zwróconą przez Whispera (mock).
        """
        self.mock_model.transcribe.return_value = {"text": " integration transcript "}

        result_path = stt_services.transcribe_audio_to_file(
            str(self.audio_path),
            overwrite=True,
        )

        self.assertEqual(Path(result_path), self.transcript_path.resolve())
        self.assertTrue(self.transcript_path.exists())
        self.assertEqual(
            self.transcript_path.read_text(encoding="utf-8"),
            "integration transcript",
        )
        self.mock_model.transcribe.assert_called_once()

    def test_transcribe_video_end_to_end_uses_existing_audio_and_updates_video(self):
        """
        Tworzy Video wskazujące na prawdziwy plik audio w media/audio,
        wywołuje transcribe_video i sprawdza:
        - utworzenie pliku transkrypcji w media/transcripts,
        - ustawienie video.transcript_path w obiekcie i w bazie.
        """
        video = Video.objects.create(
            url="https://example.com/fLeJJPxua3E",
            platform="other",
            audio_path=str(self.audio_path.resolve()),
        )

        self.assertFalse(video.transcript_path)

        self.mock_model.transcribe.return_value = {"text": "video integration transcript"}

        updated = stt_services.transcribe_video(video, force=False)

        self.assertTrue(self.transcript_path.exists())
        self.assertEqual(
            self.transcript_path.read_text(encoding="utf-8"),
            "video integration transcript",
        )

        self.assertEqual(updated.transcript_path, str(self.transcript_path.resolve()))
        video.refresh_from_db()
        self.assertEqual(video.transcript_path, str(self.transcript_path.resolve()))

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

    def test_real_whisper_transcription_on_existing_audio(self):
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

    def test_transcribe_audio_to_file_raises_if_audio_missing(self):
        missing_path = self.audio_dir / "missing.mp3"
        with self.assertRaises(FileNotFoundError):
            stt_services.transcribe_audio_to_file(str(missing_path))

    def test_transcribe_audio_to_file_returns_existing_when_not_overwrite(self):
        audio_path = self.audio_dir / "file.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        transcript_path.write_text("existing transcript", encoding="utf-8")

        result = stt_services.transcribe_audio_to_file(str(audio_path), overwrite=False)

        self.assertEqual(Path(result), transcript_path.resolve())
        # Nie powinniśmy w ogóle wołać transcribe na modelu
        self.mock_model.transcribe.assert_not_called()

    def test_transcribe_audio_to_file_creates_transcript_and_calls_model(self):
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

    # ... existing code ...

    def test_transcribe_audio_to_file_wraps_file_not_found_from_whisper(self):
        """
        Gdy _model.transcribe rzuci FileNotFoundError (np. brak ffmpeg/ffprobe),
        funkcja powinna owinąć to w RuntimeError z odpowiednim komunikatem.
        """
        audio_path = self.audio_dir / "file3.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        # Symulujemy błąd na poziomie Whispera
        self.mock_model.transcribe.side_effect = FileNotFoundError("ffmpeg not found")

        with self.assertRaises(RuntimeError) as ctx:
            stt_services.transcribe_audio_to_file(str(audio_path), overwrite=True)

        msg = str(ctx.exception)
        self.assertIn("Nie udało się wczytać audio – sprawdź czy ffmpeg/ffprobe są zainstalowane i w PATH.", msg)

        # Nie powinno powstać żadne wyjście transkrypcji
        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        self.assertFalse(transcript_path.exists())

    def test_transcribe_audio_to_file_wraps_generic_exception_from_whisper(self):
        """
        Gdy _model.transcribe rzuci dowolny inny wyjątek,
        funkcja powinna rzucić RuntimeError z komunikatem 'Transkrypcja nie powiodła się: ...'.
        """
        audio_path = self.audio_dir / "file4.mp3"
        audio_path.write_text("dummy audio", encoding="utf-8")

        self.mock_model.transcribe.side_effect = Exception("GPU out of memory")

        with self.assertRaises(RuntimeError) as ctx:
            stt_services.transcribe_audio_to_file(str(audio_path), overwrite=True)

        msg = str(ctx.exception)
        self.assertIn("Transkrypcja nie powiodła się: GPU out of memory", msg)

        transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
        self.assertFalse(transcript_path.exists())
