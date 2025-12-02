import os
from typing import Dict, List

from groq import Groq


_client: Groq | None = None


def _get_client() -> Groq:
    """
    Tworzy (leniwe) jednoinstancyjnego klienta Groq.
    Wymaga zmiennej środowiskowej GROQ_API_KEY.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Brak zmiennej środowiskowej GROQ_API_KEY")
        _client = Groq(api_key=api_key)
    return _client


def _build_summary_prompt(nlp_results: Dict) -> str:
    """
    Buduje prosty tekst z wyników analizy, który przekażemy do Groqa.
    """
    overall = nlp_results.get("overall") or {}
    features: List[Dict] = nlp_results.get("features") or []

    lines: List[str] = []

    lines.append(
        f"Ocena ogólna: label={overall.get('label', 'NEUTRAL')}, "
        f"score={float(overall.get('score', 0.5)):.3f}"
    )
    lines.append("Cechy telefonu:")

    for f in features:
        lines.append(
            f"- cecha={f.get('feature', '?')}, "
            f"label={f.get('label', 'NEUTRAL')}, "
            f"score={float(f.get('score', 0.5)):.3f}, "
            f"summary=\"{f.get('summary', '').strip()}\""
        )

    return "\n".join(lines)


def summarize_nlp_results(nlp_results: Dict) -> str:
    """
    Wywołuje Groqa i zwraca krótkie, zrozumiałe dla laika podsumowanie.
    """
    client = _get_client()
    prompt = _build_summary_prompt(nlp_results)

    system_msg = (
        "Jesteś asystentem, który tłumaczy wyniki analizy sentymentu "
        "w prostym, zrozumiałym języku po polsku. "
        "Piszesz zwięzłe podsumowania (maksymalnie 5 krótkich zdań), "
        "bez żargonu technicznego."
    )

    user_msg = (
        "Na podstawie poniższych danych z analizy sentymentu napisz krótkie "
        "podsumowanie recenzji telefonu dla osoby nietechnicznej. "
        "Najpierw ogólne wrażenie, potem jednym zdaniem wspomnij o najważniejszych "
        "cechach (tylko te, które są najbardziej pozytywne lub najbardziej negatywne).\n\n"
        + prompt
    )

    chat_completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
        max_tokens=250,
    )

    return chat_completion.choices[0].message.content.strip()
