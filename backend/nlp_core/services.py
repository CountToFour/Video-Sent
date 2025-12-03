import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from transformers import pipeline

try:
    import spacy
    _SPACY_AVAILABLE = True
except Exception:
    spacy = None  # type: ignore
    _SPACY_AVAILABLE = False


# Słownik cech i ich słów-kluczy (możesz rozszerzać)
FEATURE_KEYWORDS: Dict[str, List[str]] = {
    "bateria": [
        "bateria", "akumulator", "czas pracy", "czas działania", "czas na baterii",
        "czas screen on", "sot", "screen on time", "ładowanie", "ładowarka",
        "szybkie ładowanie", "fast charge", "qc", "power delivery", "pd",
        "ładowanie bezprzewodowe", "ładowanie indukcyjne", "qi",
        "powerbank", "wytrzymałość baterii", "zużycie energii"
    ],

    "aparat": [
        "aparat", "kamera", "kamerka", "moduł aparatu", "obiektyw", "sensor",
        "zdjęcia", "fotki", "fotografia", "fotka", "wideo", "nagrywanie",
        "video", "4k", "8k", "tryb nocny", "night mode", "hdr", "ostrość",
        "stabilizacja", "ois", "eis", "zoom", "szeroki kąt", "ultrawide",
        "selfie", "przednia kamera", "tryb portretowy"
    ],

    "ekran": [
        "ekran", "wyświetlacz", "display", "oled", "amoled", "lcd", "ips",
        "rozdzielczość", "full hd", "quad hd", "qhd", "4k",
        "jasność", "nits", "kolory", "odświeżanie", "144hz", "120hz", "90hz",
        "pwm", "kontrast", "dotyk", "responsywność ekranu", "zakrzywiony ekran",
        "proporcje ekranu"
    ],

    "wydajność": [
        "wydajność", "szybkość", "procesor", "cpu", "gpu", "chip", "chipset",
        "lag", "lagi", "zacięcia", "przycięcia", "płynność", "benchmark",
        "antutu", "geekbench", "ram", "przegrzewanie", "thermals",
        "wydajność w grach", "fps", "opóźnienia", "responsywność"
    ],

    "jakość": [
        "jakość", "wykonanie", "materiały", "obudowa", "design", "estetyka",
        "aluminium", "plastik", "szkło", "ergonomia", "wytrzymałość", "solidność",
        "certyfikat ip", "wodoodporność", "pyłoszczelność"
    ],

    "dźwięk": [
        "głośnik", "głośniki", "audio", "dźwięk", "brzmienie", "jakość dźwięku",
        "stereo", "dolby", "dolby atmos", "słuchawki", "jack", "3.5mm",
        "mikrofon", "mikrofony", "połączenia głosowe", "rozmowy"
    ],

    "system": [
        "android", "ios", "system", "aktualizacje", "update", "nakładka",
        "one ui", "miui", "hyperos", "coloros", "oxygenos", "pixel experience",
        "stabilność systemu", "błędy systemu", "bugi", "aktualizacja bezpieczeństwa"
    ],

    "pamięć": [
        "pamięć", "ram", "rom", "magazyn", "magazynowanie", "miejsce",
        "pamięć wewnętrzna", "storage", "micro sd", "karta pamięci",
        "przestrzeń", "zajęte miejsce", "przechowywanie danych"
    ],

    "cena": [
        "cena", "koszt", "drogi", "tani", "budżetowy", "opłacalność",
        "stosunek jakości do ceny", "value", "przepłacony", "taniocha",
        "promocja", "oferta", "wartość"
    ],

    "łączność": [
        "wifi", "bluetooth", "5g", "lte", "4g", "zasięg", "modem",
        "nfc", "gps", "galileo", "wifi calling", "volte", "esim", "dual sim",
        "usb c", "usb-c", "otg"
    ],

    "ogólne wrażenia": [
        "ogólnie", "wrażenia", "użytkowanie", "komfort", "codzienne użytkowanie",
        "doświadczenie", "feel", "wygoda", "satysfakcja", "zadowolenie"
    ],
}

# Model sentymentu: wielojęzyczny 1-5 gwiazdek (obsługuje PL); prosty w użyciu
_SENTIMENT_MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

_nlp = None
_sentiment_pipe = None


def _load_spacy_pl():
    """
    Inicjalizacja spaCy do tokenizacji/zdaniowania.
    Najpierw próbujemy pl_core_news_sm, jeśli brak – fallback na blank('pl') + sentencizer.
    """
    global _nlp
    if _nlp is not None:
        return _nlp

    if _SPACY_AVAILABLE:
        try:
            _nlp = spacy.load("pl_core_news_sm")
        except Exception:
            # Fallback: brak modelu – użyjemy prostego sentencizera
            _nlp = spacy.blank("pl")
            if "sentencizer" not in _nlp.pipe_names:
                _nlp.add_pipe("sentencizer")
    else:
        _nlp = None
    return _nlp


def _load_sentiment_pipeline():
    global _sentiment_pipe
    if _sentiment_pipe is not None:
        return _sentiment_pipe
    try:
        _sentiment_pipe = pipeline("sentiment-analysis", model=_SENTIMENT_MODEL_NAME)
    except Exception as e:
        # Brak internetu/cache albo inny problem z modelem
        raise RuntimeError(
            f"Nie można zainicjalizować modelu sentymentu '{_SENTIMENT_MODEL_NAME}'. "
            f"Sprawdź połączenie/środowisko. Szczegóły: {e}"
        )
    return _sentiment_pipe


def _split_sentences(text: str) -> List[str]:
    nlp = _load_spacy_pl()
    if nlp:
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents if s.text.strip()]
        if sents:
            return sents
    # bardzo prosty fallback, gdyby spaCy zawiodło
    sents = re.split(r"(?<=[\.\!\?])\s+", text)
    return [s.strip() for s in sents if s.strip()]


def _contains_keyword(sentence: str, keyword: str) -> bool:
    s = sentence.lower()
    k = keyword.lower()
    # prosty contains + granice słów, jeśli to 1-2 wyrazy
    if " " in k:
        return k in s
    return re.search(rf"\b{re.escape(k)}\b", s) is not None


@dataclass
class SentimentResult:
    label: str  # NEGATIVE | NEUTRAL | POSITIVE
    score: float  # 0..1 (pozytywność)
    raw_label: str  # np. "4 stars"
    raw_score: float


def _map_stars_to_result(raw_label: str, raw_score: float) -> SentimentResult:
    """
    Model zwraca etykiety '1 star' ... '5 stars'.
    Mapujemy do NEGATIVE/NEUTRAL/POSITIVE oraz obliczamy pozytywność: (stars-1)/4.
    """
    m = re.search(r"(\d)", raw_label)
    stars = int(m.group(1)) if m else 3
    pos_score = max(0.0, min(1.0, (stars - 1) / 4.0))
    if stars <= 2:
        label = "NEGATIVE"
    elif stars == 3:
        label = "NEUTRAL"
    else:
        label = "POSITIVE"
    return SentimentResult(label=label, score=pos_score, raw_label=raw_label, raw_score=raw_score)

def _predict_batch(texts: List[str]):
    """
    Bezpieczne wywołanie pipeline na batchu z truncation=True.
    """
    sentiment = _load_sentiment_pipeline()
    return sentiment(texts, truncation=True)

def _overall_from_chunks(text: str, max_chunk_chars: int = 900) -> SentimentResult:
    """
    Dzieli tekst na krótsze kawałki i uśrednia pozytywność.
    Dzięki temu unikamy błędów długości wejścia modelu.
    """
    if not text:
        return SentimentResult(label="NEUTRAL", score=0.5, raw_label="3 stars", raw_score=0.0)

    # Podział po zdaniach, a następnie łączenie w kawałki do ~max_chunk_chars
    sentences = _split_sentences(text)
    chunks: List[str] = []
    buf = ""
    for s in sentences:
        sep = " " if buf else ""
        if len(buf) + len(sep) + len(s) <= max_chunk_chars:
            buf = f"{buf}{sep}{s}" if buf else s
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)

    # Jeszcze bezpieczniej: jeśli i tak wyszło pusto
    if not chunks:
        chunks = [text[:max_chunk_chars]]

    preds = _predict_batch(chunks)
    pos = []
    for p in preds:
        res = _map_stars_to_result(p["label"], p.get("score", 0.0))
        pos.append(res.score)
    avg = sum(pos) / len(pos)
    if avg < 0.4:
        label = "NEGATIVE"
    elif avg > 0.6:
        label = "POSITIVE"
    else:
        label = "NEUTRAL"
    return SentimentResult(label=label, score=avg, raw_label="avg-stars", raw_score=0.0)



def analyze_text(text: str) -> Dict:
    """
    Zwraca:
    {
      "overall": {"label": str, "score": float},
      "features": [{"feature": str, "label": str, "score": float, "summary": str}]
    }
    """
    if not text or not text.strip():
        return {"overall": {"label": "NEUTRAL", "score": 0.5}, "features": []}

    try:
        sentences = _split_sentences(text)
        # overall na bazie chunków (bezpieczniej)
        ov_res = _overall_from_chunks(text)

        # indeksowanie zdań przez cechy
        feature_sentences: Dict[str, List[str]] = defaultdict(list)
        for feat, keys in FEATURE_KEYWORDS.items():
            for sent in sentences:
                if any(_contains_keyword(sent, kw) for kw in keys):
                    feature_sentences[feat].append(sent)

        # analiza sentymentu per cecha
        feature_results = []
        for feat, sents in feature_sentences.items():
            preds = _predict_batch(sents)  # truncation=True w środku
            scores = []
            pos_scores = []
            for pred in preds:
                res = _map_stars_to_result(pred["label"], pred.get("score", 0.0))
                pos_scores.append(res.score)
                scores.append(res)
            if not scores:
                continue
            avg_pos = sum(pos_scores) / len(pos_scores)
            # prosta decyzja progowa
            if avg_pos < 0.4:
                agg_label = "NEGATIVE"
            elif avg_pos > 0.6:
                agg_label = "POSITIVE"
            else:
                agg_label = "NEUTRAL"

            # krótkie podsumowanie: pierwsze (do 2) najbardziej reprezentatywne zdania
            summary = " ".join(sents[:2])[:255]
            feature_results.append({
                "feature": feat,
                "label": agg_label,
                "score": round(avg_pos, 4),
                "summary": summary or f"Wzmianki o {feat}."
            })

        # sort po ważności (najpierw te z większą liczbą zdań, potem po score)
        feature_results.sort(key=lambda x: (len(feature_sentences[x["feature"]]), x["score"]), reverse=True)

        if feature_results:
            feature_scores = [fr["score"] for fr in feature_results]
            avg_overall = sum(feature_scores) / len(feature_scores)
            if avg_overall < 0.4:
                overall_label = "NEGATIVE"
            elif avg_overall > 0.6:
                overall_label = "POSITIVE"
            else:
                overall_label = "NEUTRAL"
            overall = {
                "label": overall_label,
                "score": round(avg_overall, 4),
            }
        else:
            # fallback, gdy nie wykryto żadnych cech – użyj wyniku z chunków
            overall = {
                "label": ov_res.label,
                "score": round(ov_res.score, 4),
            }

        return {
            "overall": overall,
            "features": feature_results,
        }

    except RuntimeError as e:
        # problem z inicjalizacją modelu
        return {
            "overall": {"label": "NEUTRAL", "score": 0.5},
            "features": [],
            "warning": f"Analiza w trybie uproszczonym (model niedostępny): {e}",
        }
    except Exception as e:
        # jakikolwiek inny błąd – nie wywracaj endpointu
        return {
            "overall": {"label": "NEUTRAL", "score": 0.5},
            "features": [],
            "warning": f"Analiza w trybie awaryjnym: {e}",
        }



# Integracja z bazą (FeatureSentiment)
def save_results_for_video(video, results: Dict):
    """
    Tworzy/aktualizuje FeatureSentiment dla podanego Video na podstawie wyników.
    """
    from nlp_core.models import FeatureSentiment, SentimentLabel  # import lokalny, aby uniknąć cykli

    for fr in results.get("features", []):
        feat = fr["feature"]
        label = fr["label"]
        score = float(fr["score"])
        summary = fr["summary"]

        fs, _created = FeatureSentiment.objects.update_or_create(
            video=video,
            feature=feat,
            defaults={
                "sentiment": label if label in SentimentLabel.values else SentimentLabel.NEUTRAL,
                "score": score,
                "summary": summary[:255],
            }
        )

    return True