from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from downloader.models import Video
from nlp_core.models import FeatureSentiment

class Command(BaseCommand):
    help = "Seed initial data"

    def handle(self, *args, **options):
        if not User.objects.filter(username="test1").exists():
            User.objects.create_user(username="test1", password="pass123")
            User.objects.create_user(username="test2", password="pass123")
        if Video.objects.count() == 0:
            video = Video.objects.create(url='https://www.youtube.com/watch?v=3bhmtb_ouI8',
                             platform='youtube',
                             title='SENTINO - Lato prod. CrackHouse')
        else:
            video = Video.objects.first()

        if FeatureSentiment.objects.count() == 0:
            FeatureSentiment.objects.create(video=video,
                                            feature='Example feature',
                                            sentiment='NEUTRAL',
                                            summary='lorem ipsum bla bla bla')
