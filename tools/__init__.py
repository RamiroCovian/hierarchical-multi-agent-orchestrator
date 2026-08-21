"""Herramientas acotadas por rol para los agentes especialistas."""

from tools.analysis import (
    ANALYST_TOOLS,
    analyze_sentiment,
    extract_key_points,
    validate_json_payload,
)
from tools.research import RESEARCH_TOOLS, web_search

__all__ = [
    "web_search",
    "analyze_sentiment",
    "extract_key_points",
    "validate_json_payload",
    "RESEARCH_TOOLS",
    "ANALYST_TOOLS",
]
