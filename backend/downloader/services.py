import os
from pathlib import Path

import yt_dlp
from yt_dlp import DownloadError

from .models import Video, Platform

BASE_MEDIA = Path("media")
AUDIO_DIR = BASE_MEDIA / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return Platform.YOUTUBE
    if "tiktok.com" in url_lower:
        return Platform.TIKTOK
    if "instagram.com" in url_lower:
        return Platform.INSTAGRAM
    return Platform.OTHER


def download_audio_with_ytdlp(url: str) -> tuple[str, str]:
    """
    Pobiera audio z URLa i zwraca (title, audio_path).
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(AUDIO_DIR / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

    except DownloadError as e:
        error_msg = str(e).lower()
        if "video unavailable" in error_msg:
            raise ValueError("Podany film jest niedostępny (usunięty lub nieprawidłowy link).")
        else:
            raise ValueError(f"Nie udało się pobrać wideo: {e}")

    video_id = info.get("id")
    candidate = AUDIO_DIR / f"{video_id}.mp3"
    if candidate.exists():
        final_path = candidate
    else:
        # fallback, gdyby nazwa była inna
        filename = ydl.prepare_filename(info)
        final_path = Path(filename)
        if not final_path.exists():
            raise FileNotFoundError("Nie udało się zlokalizować pobranego audio.")

    title = info.get("title") or url
    return title, str(final_path.resolve())


def get_or_create_video_with_audio(url: str) -> Video:
    """
    Tworzy lub aktualizuje Video:
    - ustawia platform,
    - pobiera audio (jeśli brak),
    - zapisuje audio_path.
    """

    platform = detect_platform(url)
    if platform != Platform.YOUTUBE:
        raise ValueError("Obsługiwane są wyłącznie linki z YouTube (youtube.com).")

    try:
        video = Video.objects.get(url=url)
    except Video.DoesNotExist:
        video = Video(url=url, platform=platform)

    if not video.audio_path:
        title, audio_path = download_audio_with_ytdlp(url)
        video.title = title
        video.audio_path = audio_path
        video.platform = detect_platform(url)
        video.save()

    return video
