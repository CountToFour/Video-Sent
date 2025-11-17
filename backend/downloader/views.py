from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Video
from .serializers import VideoSerializer  # zakładam, że masz taki serializer
from .services import get_or_create_video_with_audio
from speech_to_text.services import transcribe_video


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all().order_by("-created_at")
    serializer_class = VideoSerializer

    @action(detail=False, methods=["post"])
    def from_url(self, request):
        """
        Body: { "url": "https://..." }
        Pipeline:
        - Video + audio (yt-dlp)
        - transkrypcja
        - zwraca Video z transcript_path.
        """
        url = request.data.get("url")
        if not url:
            return Response(
                {"detail": "URL is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            video = get_or_create_video_with_audio(url)
            video = transcribe_video(video)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(video)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def transcript(self, request, pk=None):
        """
        GET /api/videos/{id}/transcript/
        Zwraca tekst transkrypcji jako JSON: { "transcript": "..." }
        """
        video = self.get_object()

        if not video.transcript_path:
            return Response(
                {"detail": "Transkrypcja niedostępna."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            with open(video.transcript_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return Response(
                {"detail": "Plik transkrypcji nie istnieje."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"transcript": content}, status=status.HTTP_200_OK)
