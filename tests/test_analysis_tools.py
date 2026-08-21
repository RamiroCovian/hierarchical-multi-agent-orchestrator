"""Tests de herramientas de análisis (deterministas)."""

from tools.analysis import analyze_sentiment, extract_key_points, validate_json_payload


def test_analyze_sentiment_positive():
    result = analyze_sentiment.invoke({"text": "Excelente mejora y gran oportunidad"})
    assert "positivo" in result


def test_analyze_sentiment_negative():
    result = analyze_sentiment.invoke({"text": "Hay un problema grave y una crisis"})
    assert "negativo" in result


def test_analyze_sentiment_empty():
    result = analyze_sentiment.invoke({"text": "   "})
    assert result.startswith("Error:")


def test_extract_key_points_returns_structure():
    result = extract_key_points.invoke(
        {
            "text": "LangGraph orquesta agentes. Facilita el control de flujo. Escala bien.",
            "top_n": 3,
        }
    )
    assert "Puntos clave:" in result
    assert "Términos frecuentes:" in result


def test_validate_json_payload_valid():
    result = validate_json_payload.invoke(
        {
            "data_json": '{"title": "x", "score": 1}',
            "required_fields": "title,score",
        }
    )
    assert result.startswith("Válido:")


def test_validate_json_payload_missing_fields():
    result = validate_json_payload.invoke(
        {
            "data_json": '{"title": "x"}',
            "required_fields": "title,score",
        }
    )
    assert "faltan campos" in result


def test_validate_json_payload_malformed():
    result = validate_json_payload.invoke(
        {
            "data_json": "{no-json",
            "required_fields": "title",
        }
    )
    assert result.startswith("Inválido:")
