from rest_framework import viewsets
from .models import Transcript
from .serializers import TranscriptSerializer

class TranscriptViewSet(viewsets.ModelViewSet):
    queryset = Transcript.objects.all()
    serializer_class = TranscriptSerializer