from rest_framework import viewsets
from .models import FeatureSentiment
from .serializers import FeatureSentimentSerializer


from rest_framework import viewsets
from .models import FeatureSentiment
from .serializers import FeatureSentimentSerializer
# ... existing code ...
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from downloader.models import Video
from django.utils.encoding import force_str

from . import services
# ... existing code ...


class FeatureSentimentViewSet(viewsets.ModelViewSet):
    queryset = FeatureSentiment.objects.all()
    serializer_class = FeatureSentimentSerializer
# ... existing code ...


class AnalyzeView(APIView):
    """
    POST /api/nlp/analyze/
    Body:
      - { "video_id": int }  -> odczytuje transkrypcję z pliku Video.transcript_path
      - lub { "text": "..." } -> analizuje podany tekst
    Zwraca:
      {
        "overall": {"label": "...", "score": 0.x},
        "features": [{"feature": "...", "label": "...", "score": 0.x, "summary": "..."}]
      }
    Jeśli podano video_id, zapisuje/aktualizuje wpisy FeatureSentiment w DB.
    """
    def post(self, request):
        video_id = request.data.get("video_id")
        text = request.data.get("text")

        transcript_text = None
        video = None

        if video_id is not None:
            try:
                video = Video.objects.get(pk=video_id)
            except Video.DoesNotExist:
                return Response({"detail": "Video nie istnieje."}, status=status.HTTP_404_NOT_FOUND)

            if not video.transcript_path:
                return Response({"detail": "Brak transkrypcji dla tego nagrania."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                with open(video.transcript_path, "r", encoding="utf-8") as f:
                    transcript_text = f.read()
            except FileNotFoundError:
                return Response({"detail": "Plik transkrypcji nie istnieje."}, status=status.HTTP_404_NOT_FOUND)

        if transcript_text is None:
            if not text or not force_str(text).strip():
                return Response({"detail": "Wymagane video_id lub text."}, status=status.HTTP_400_BAD_REQUEST)
            transcript_text = force_str(text)

        try:
            results = services.analyze_text(transcript_text)
        except Exception as e:
            return Response({"detail": f"Błąd analizy: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if video is not None:
            try:
                services.save_results_for_video(video, results)
            except Exception as e:
                # Zwracamy mimo wszystko wyniki, ale sygnalizujemy błąd zapisu
                return Response({
                    "detail": f"Wyniki wygenerowane, ale błąd zapisu do DB: {e}",
                    "results": results
                }, status=status.HTTP_207_MULTI_STATUS)

        return Response(results, status=status.HTTP_200_OK)