import json
from django.http import StreamingHttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Video
from .serializers import VideoSerializer
from .services import get_or_create_video_with_audio
from speech_to_text.services import transcribe_video
from nlp_core import services as nlp_services
from nlp_core.groq_summary import summarize_nlp_results


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

        def event_stream():
            try:
                yield json.dumps({
                    "type": "progress",
                    "message": "Inicjalizacja...",
                    "progress": 5
                }) + "\n"

                yield json.dumps({
                    "type": "progress",
                    "message": "Pobieranie audio z YouTube...",
                    "progress": 20
                }) + "\n"

                video = get_or_create_video_with_audio(url)

                yield json.dumps({
                    "type": "progress",
                    "message": "Transkrypcja audio (to może potrwać)...",
                    "progress": 50
                }) + "\n"

                video = transcribe_video(video)

                if not video.transcript_path:
                    raise Exception("Transkrypcja nie powiodła się.")

                with open(video.transcript_path, "r", encoding="utf-8") as f:
                    text = f.read()

                yield json.dumps({
                    "type": "progress",
                    "message": "Analiza sentymentu i generowanie podsumowania...",
                    "progress": 85
                }) + "\n"

                nlp_results = nlp_services.analyze_text(text)
                try:
                    nlp_results["user_summary"] = summarize_nlp_results(nlp_results)
                except Exception:
                    nlp_results["user_summary"] = None

                nlp_services.save_results_for_video(video, nlp_results)

                yield json.dumps({
                    "type": "progress",
                    "message": "Gotowe!",
                    "progress": 100
                }) + "\n"

                serializer = VideoSerializer(video)
                data = serializer.data
                data["nlp_results"] = nlp_results

                yield json.dumps({"type": "complete", "data": data}) + "\n"

            except Exception as e:
                yield json.dumps({"type": "error", "message": str(e)}) + "\n"

        return StreamingHttpResponse(event_stream(), content_type="application/x-ndjson")

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
