from pathlib import Path

import whisper

from downloader.models import Video

BASE_MEDIA = Path("media")
TRANSCRIPTS_DIR = BASE_MEDIA / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Ładujemy model przy starcie (dla dev np. "base"; można zmienić na "small"/"medium").
_model = whisper.load_model("base")


def transcribe_audio_to_file(audio_path: str, overwrite: bool = False) -> str:
    """
    Transkrybuje audio i zapisuje tekst do pliku .txt.
    Zwraca pełną ścieżkę do pliku transkrypcji.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    transcript_path = TRANSCRIPTS_DIR / f"{audio_path.stem}.txt"
    if transcript_path.exists() and not overwrite:
        return str(transcript_path.resolve())

    try:
        result = _model.transcribe(str(audio_path), fp16=False)
    except FileNotFoundError as e:
        raise RuntimeError(
            "Nie udało się wczytać audio – sprawdź czy ffmpeg/ffprobe są zainstalowane i w PATH."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Transkrypcja nie powiodła się: {e}") from e

    text = (result.get("text") or "").strip()

    transcript_path = TRANSCRIPTS_DIR / f"{audio_path.stem}.txt"
    transcript_path.write_text(text, encoding="utf-8")

    return str(transcript_path.resolve())


def transcribe_video(video: Video, force: bool = False) -> Video:
    """
    - Wymaga ustawionego video.audio_path.
    - Tworzy transkrypcję i zapisuje ścieżkę w video.transcript_path.
    """
    if not video.audio_path:
        raise ValueError("Brak audio_path. Najpierw pobierz audio.")

    audio_path = Path(video.audio_path)
    expected_transcript = TRANSCRIPTS_DIR / f"{audio_path.stem}.txt"

    # Przypadek: pole ustawione i plik istnieje -> zwracamy jak jest (chyba że force)
    if video.transcript_path:
        existing = Path(video.transcript_path)
        if existing.exists() and not force:
            return video

    if not video.transcript_path and expected_transcript.exists() and not force:
        video.transcript_path = str(expected_transcript.resolve())
        video.save(update_fields=["transcript_path"])
        return video

    transcript_path = transcribe_audio_to_file(str(audio_path), overwrite=force)
    video.transcript_path = transcript_path
    video.save(update_fields=["transcript_path"])
    return video
