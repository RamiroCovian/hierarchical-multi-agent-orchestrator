"""Herramientas de análisis y cómputo."""

import json
import re
from collections import Counter

from langchain_core.tools import tool

_POSITIVE_WORDS = {
    "bueno",
    "buena",
    "excelente",
    "positivo",
    "positiva",
    "éxito",
    "exito",
    "crecimiento",
    "mejora",
    "oportunidad",
    "favorable",
    "sólido",
    "solido",
    "fortaleza",
    "avance",
    "beneficio",
}

_NEGATIVE_WORDS = {
    "malo",
    "mala",
    "negativo",
    "negativa",
    "riesgo",
    "problema",
    "crisis",
    "caída",
    "caida",
    "pérdida",
    "perdida",
    "falla",
    "amenaza",
    "débil",
    "debil",
    "preocupante",
    "insuficiente",
}


@tool
def analyze_sentiment(text: str) -> str:
    """Analiza el sentimiento de un texto (positivo, negativo o neutro).

    Args:
        text: Texto a evaluar, por ejemplo hallazgos de investigación.
    """
    if not text.strip():
        return "Error: el texto a analizar no puede estar vacío."

    tokens = re.findall(r"[a-záéíóúñü]+", text.lower())
    if not tokens:
        return "Sentimiento: neutro | score: 0 | detalle: sin palabras analizables"

    positive_hits = [token for token in tokens if token in _POSITIVE_WORDS]
    negative_hits = [token for token in tokens if token in _NEGATIVE_WORDS]
    score = len(positive_hits) - len(negative_hits)

    if score > 0:
        label = "positivo"
    elif score < 0:
        label = "negativo"
    else:
        label = "neutro"

    return (
        f"Sentimiento: {label} | score: {score} | "
        f"positivos: {len(positive_hits)} | negativos: {len(negative_hits)}"
    )


@tool
def extract_key_points(text: str, top_n: int = 5) -> str:
    """Extrae puntos clave y palabras frecuentes de un texto analítico.

    Args:
        text: Texto con hallazgos o datos a resumir.
        top_n: Cantidad de términos frecuentes a devolver.
    """
    if not text.strip():
        return "Error: el texto a procesar no puede estar vacío."

    sentences = [
        sentence.strip()
        for sentence in re.split(r"[.!?]\s+", text)
        if sentence.strip()
    ]
    tokens = re.findall(r"[a-záéíóúñü]{4,}", text.lower())
    stopwords = {
        "para",
        "como",
        "esta",
        "este",
        "estos",
        "estas",
        "sobre",
        "desde",
        "hasta",
        "entre",
        "según",
        "segun",
        "también",
        "tambien",
        "donde",
        "cuando",
        "porque",
        "tiene",
        "tienen",
        "puede",
        "pueden",
        "hacia",
    }
    filtered = [token for token in tokens if token not in stopwords]
    common = Counter(filtered).most_common(max(top_n, 1))

    key_sentences = sentences[:3] or ["Sin oraciones detectadas"]
    terms = ", ".join(f"{word} ({count})" for word, count in common) or "N/A"

    lines = [
        "Puntos clave:",
        *[f"- {sentence}" for sentence in key_sentences],
        f"Términos frecuentes: {terms}",
        f"Estadísticas: {len(tokens)} tokens | {len(sentences)} oraciones",
    ]
    return "\n".join(lines)


@tool
def validate_json_payload(data_json: str, required_fields: str) -> str:
    """Valida que un JSON tenga los campos requeridos.

    Args:
        data_json: Objeto JSON a validar (como string).
        required_fields: Campos obligatorios separados por coma.
    """
    if not data_json.strip():
        return "Error: data_json no puede estar vacío."

    try:
        payload = json.loads(data_json)
    except json.JSONDecodeError as error:
        return f"Inválido: JSON malformado ({error})"

    if not isinstance(payload, dict):
        return "Inválido: se esperaba un objeto JSON (dict)."

    fields = [field.strip() for field in required_fields.split(",") if field.strip()]
    if not fields:
        return "Error: indicá al menos un campo requerido."

    missing = [field for field in fields if field not in payload]
    if missing:
        return f"Inválido: faltan campos {', '.join(missing)}"

    return f"Válido: contiene los campos requeridos ({', '.join(fields)})"


ANALYST_TOOLS = [analyze_sentiment, extract_key_points, validate_json_payload]
