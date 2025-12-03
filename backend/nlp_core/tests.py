import os
import tempfile
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from downloader.models import Video
from nlp_core import services
from nlp_core.groq_summary import _get_client, _build_summary_prompt, summarize_nlp_results
from nlp_core.models import FeatureSentiment
from nlp_core.services import _split_sentences


class SplitSentencesTests(TestCase):

    @patch("nlp_core.services._load_spacy_pl")
    def test_split_sentences_with_spacy(self, mock_load_spacy):
        # Mock spaCy nlp() and its doc.sents
        mock_nlp = MagicMock()
        mock_doc = MagicMock()

        mock_doc.sents = [
            MagicMock(text="To jest pierwsze zdanie."),
            MagicMock(text="A to drugie zdanie!"),
        ]

        mock_nlp.return_value = mock_doc
        mock_load_spacy.return_value = mock_nlp

        text = "To jest pierwsze zdanie. A to drugie zdanie!"

        result = _split_sentences(text)

        self.assertEqual(
            result,
            ["To jest pierwsze zdanie.", "A to drugie zdanie!"]
        )

    @patch("nlp_core.services._load_spacy_pl", return_value=None)
    def test_split_sentences_fallback(self, mock_load_spacy):
        text = "Ala ma kota. Kot ma Ale? Super!"

        result = _split_sentences(text)

        self.assertEqual(
            result,
            ["Ala ma kota.", "Kot ma Ale?", "Super!"]
        )


class TestSentimentPipeline(TestCase):

    @patch("nlp_core.services.pipeline")
    def test_load_sentiment_pipeline_ok(self, mock_pipeline):
        services._sentiment_pipe = None  # reset

        fake_pipe = MagicMock()
        mock_pipeline.return_value = fake_pipe

        res = services._load_sentiment_pipeline()

        mock_pipeline.assert_called_once_with(
            "sentiment-analysis",
            model=services._SENTIMENT_MODEL_NAME
        )
        self.assertIs(res, fake_pipe)

    @patch("nlp_core.services.pipeline")
    def test_load_sentiment_pipeline_error(self, mock_pipeline):
        services._sentiment_pipe = None

        mock_pipeline.side_effect = Exception("Model not found")

        with self.assertRaises(RuntimeError) as ctx:
            services._load_sentiment_pipeline()

        self.assertIn("Nie można zainicjalizować modelu sentymentu", str(ctx.exception))


class TestLoadSpacy(TestCase):

    @patch("nlp_core.services.spacy")
    @patch("nlp_core.services._SPACY_AVAILABLE", True)
    def test_load_spacy_ok(self, mock_spacy):
        mock_nlp = MagicMock()
        mock_spacy.load.return_value = mock_nlp

        res = services._load_spacy_pl()
        self.assertIs(res, mock_nlp)

    @patch("nlp_core.services.spacy.load")
    @patch("nlp_core.services.spacy.blank")
    def test_load_spacy_unavailable(self, mock_blank, mock_load):
        from nlp_core import services

        services._nlp = None

        # load rzuca wyjątek → fallback
        mock_load.side_effect = Exception("no model")

        mock_blank_nlp = MagicMock()
        mock_blank.return_value = mock_blank_nlp

        # tak działa Twój kod
        res = services._load_spacy_pl()

        # load wywołane raz
        mock_load.assert_called_once_with("pl_core_news_sm")
        # blank wywołane jako fallback
        mock_blank.assert_called_once_with("pl")

        # wynik to obiekt blank()
        self.assertIs(res, mock_blank_nlp)


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
        import uuid

        video = Video.objects.create(
            title="Test",
            url=f"http://example.com/{uuid.uuid4()}"
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

class GetClientTest(TestCase):

    @patch.dict(os.environ, {"GROQ_API_KEY": "KEY"})
    @patch("nlp_core.groq_summary.Groq")
    def test_client_created_once(self, mock_groq):
        c1 = _get_client()
        c2 = _get_client()

        self.assertIs(c1, c2)
        mock_groq.assert_called_once_with(api_key="KEY")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        # reset globalnego klienta po poprzednim teście
        from nlp_core import groq_summary
        groq_summary._client = None

        with self.assertRaises(RuntimeError):
            _get_client()


class BuildSummaryPromptTest(TestCase):

    def test_build_prompt_basic(self):
        data = {
            "overall": {"label": "POS", "score": 0.9},
            "features": [
                {"feature": "kamera", "label": "POS", "score": 0.8, "summary": "super jakość"},
                {"feature": "bateria", "label": "NEG", "score": 0.2, "summary": "słaba"}
            ]
        }

        text = _build_summary_prompt(data)

        self.assertIn("Ocena ogólna: label=POS, score=0.900", text)
        self.assertIn("Cechy telefonu:", text)
        self.assertIn("- cecha=kamera, label=POS", text)
        self.assertIn("summary=\"super jakość\"", text)
        self.assertIn("- cecha=bateria, label=NEG", text)

    def test_build_prompt_empty(self):
        text = _build_summary_prompt({})
        self.assertIn("label=NEUTRAL", text)
        self.assertIn("score=0.500", text)
        self.assertIn("Cechy telefonu:", text)


class SummarizeNLPResultsTest(TestCase):

    @patch("nlp_core.groq_summary._get_client")
    def test_summarize_nlp_calls_groq(self, mock_client):
        # mock response structure used by Groq API
        mock_api = MagicMock()
        mock_api.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="RESULT TEXT"))]
        )

        mock_client.return_value = mock_api

        data = {"overall": {"label": "POS", "score": 0.9}}

        result = summarize_nlp_results(data)

        self.assertEqual(result, "RESULT TEXT")
        mock_api.chat.completions.create.assert_called_once()

    @patch("nlp_core.groq_summary._get_client")
    def test_summarize_built_prompt_correct(self, mock_client):
        mock_api = MagicMock()
        mock_api.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="OK"))]
        )
        mock_client.return_value = mock_api

        data = {"overall": {"label": "NEG", "score": 0.1}}
        summarize_nlp_results(data)

        args, kwargs = mock_api.chat.completions.create.call_args

        self.assertEqual(kwargs["model"], "llama-3.3-70b-versatile")
        self.assertEqual(kwargs["temperature"], 0.4)
        self.assertEqual(kwargs["max_tokens"], 250)

        messages = kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("Ocena ogólna", messages[1]["content"])
        self.assertIn("label=NEG", messages[1]["content"])

    @patch("nlp_core.groq_summary._get_client")
    def test_summarize_returns_stripped_output(self, mock_client):
        mock_api = MagicMock()
        mock_api.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="   TRIM  "))]
        )
        mock_client.return_value = mock_api

        result = summarize_nlp_results({"overall": {}})
        self.assertEqual(result, "TRIM")

