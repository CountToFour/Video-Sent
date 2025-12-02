import os
import tempfile
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from downloader.models import Video
from nlp_core.models import FeatureSentiment
from nlp_core import services


class AnalyzeTextUnitTests(TestCase):

    @patch("nlp_core.services._predict_batch")
    @patch("nlp_core.services._split_sentences")
    def test_analyze_text_basic(self, mock_split, mock_pred):
        """
        Testuje podstawową analizę tekstu z mockami pipeline i zdań.
        """
        mock_split.return_value = [
            "Bateria trzyma bardzo długo.",
            "Aparat robi świetne zdjęcia."
        ]

        # Pierwszy batch — overall
        # Drugi batch — 'bateria'
        # Trzeci batch — 'aparat'
        mock_pred.side_effect = [
            [{"label": "4 stars", "score": 0.9}],   # overall
            [{"label": "5 stars", "score": 0.95}],  # bateria
            [{"label": "4 stars", "score": 0.85}],  # aparat
        ]

        text = "Test"
        res = services.analyze_text(text)

        self.assertEqual(res["overall"]["label"], "POSITIVE")
        self.assertGreater(res["overall"]["score"], 0.5)

        features = {f["feature"]: f for f in res["features"]}

        self.assertIn("bateria", features)
        self.assertIn("aparat", features)

        self.assertEqual(features["bateria"]["label"], "POSITIVE")
        self.assertEqual(features["aparat"]["label"], "POSITIVE")


class AnalyzeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("nlp_core.services.analyze_text")
    def test_analyze_text_direct_post(self, mock_analyze):
        mock_analyze.return_value = {
            "overall": {"label": "NEUTRAL", "score": 0.5},
            "features": [],
        }

        url = reverse("nlp-analyze")
        response = self.client.post(url, {"text": "Hello world"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overall"]["label"], "NEUTRAL")
        mock_analyze.assert_called_once()

    @patch("nlp_core.services.analyze_text")
    def test_analyze_video_success(self, mock_analyze):
        mock_analyze.return_value = {
            "overall": {"label": "POSITIVE", "score": 0.7},
            "features": [
                {"feature": "bateria", "label": "POSITIVE", "score": 0.8, "summary": "ok"}
            ],
        }

        # Tworzymy plik tymczasowy z transkrypcją
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
            f.write("Test battery text")
            path = f.name

        video = Video.objects.create(
            title="Test",
            url="http://example.com",
            transcript_path=path
        )

        url = reverse("nlp-analyze")
        response = self.client.post(url, {"video_id": video.id}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overall"]["label"], "POSITIVE")

        # Czy zapisano FeatureSentiment?
        fs = FeatureSentiment.objects.filter(video=video, feature="bateria").first()
        self.assertIsNotNone(fs)
        self.assertEqual(fs.sentiment, "POSITIVE")
        self.assertAlmostEqual(fs.score, 0.8)

        os.remove(path)

    def test_video_not_found(self):
        url = reverse("nlp-analyze")
        resp = self.client.post(url, {"video_id": 999}, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_missing_text_and_video(self):
        url = reverse("nlp-analyze")
        resp = self.client.post(url, {"text": "   "}, format="json")
        self.assertEqual(resp.status_code, 400)


class SaveResultsTests(TestCase):
    def test_save_results(self):
        video = Video.objects.create(
            title="Test",
            url="http://example.com"
        )

        results = {
            "features": [
                {"feature": "bateria", "label": "POSITIVE", "score": 0.7, "summary": "good"},
                {"feature": "aparat", "label": "NEGATIVE", "score": 0.2, "summary": "bad"},
            ]
        }

        services.save_results_for_video(video, results)

        fs1 = FeatureSentiment.objects.get(video=video, feature="bateria")
        fs2 = FeatureSentiment.objects.get(video=video, feature="aparat")

        self.assertEqual(fs1.sentiment, "POSITIVE")
        self.assertEqual(fs2.sentiment, "NEGATIVE")
        self.assertAlmostEqual(fs1.score, 0.7)
        self.assertAlmostEqual(fs2.score, 0.2)
