from pathlib import Path

import whisper

from downloader.models import Video
from downloader.services import download_audio_with_ytdlp

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
    path_obj = Path(audio_path)
    transcript_path = TRANSCRIPTS_DIR / f"{path_obj.stem}.txt"

    if transcript_path.exists() and not overwrite:
        return str(transcript_path.resolve())

    try:
        if not path_obj.exists():
            raise FileNotFoundError(f"Plik audio nie istnieje: {audio_path}")

        result = _model.transcribe(str(path_obj), fp16=False)

        text = (result.get("text") or "").strip()
        transcript_path.write_text(text, encoding="utf-8")

    except Exception as e:
        raise RuntimeError(f"Błąd procesu transkrypcji: {e}") from e

    return str(transcript_path.resolve())


def transcribe_video(video: Video, force: bool = False) -> Video:
    """
    Główna funkcja sterująca.
    Sprawdza dostępność pliku i w razie potrzeby go pobiera (Self-Healing).
    """
    if not video.audio_path:
        print(f"Brak ścieżki audio dla wideo {video.id}. Próba pobrania...")
        try:
            _, new_path = download_audio_with_ytdlp(video.url)
            video.audio_path = new_path
            video.save(update_fields=["audio_path"])
        except Exception as e:
            raise ValueError(f"Nie udało się pobrać brakującego audio: {e}")

    audio_path_obj = Path(video.audio_path)

    if not audio_path_obj.exists():
        try:
            print("BRAK PLIKU VIDEO")
            _, new_path = download_audio_with_ytdlp(video.url)
            video.audio_path = new_path
            video.save(update_fields=["audio_path"])

            audio_path_obj = Path(new_path)

        except Exception as e:
            raise RuntimeError(f"Nie udało się naprawić brakującego pliku audio: {e}")

    transcript_path = transcribe_audio_to_file(str(audio_path_obj), overwrite=force)

    if video.transcript_path != transcript_path:
        video.transcript_path = transcript_path
        video.save(update_fields=["transcript_path"])

    return video
