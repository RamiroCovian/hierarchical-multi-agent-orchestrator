"""Herramientas de investigación (búsqueda web)."""

import json
import os

from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Busca información actualizada en la web usando Tavily.

    Args:
        query: Consulta de búsqueda en lenguaje natural.
        max_results: Cantidad máxima de resultados a devolver.
    """
    if not query.strip():
        return "Error: la consulta de búsqueda no puede estar vacía."

    if not os.getenv("TAVILY_API_KEY"):
        return (
            "Error: falta TAVILY_API_KEY. Configurala en el archivo .env "
            "para habilitar la búsqueda web."
        )

    from langchain_tavily import TavilySearch

    search = TavilySearch(max_results=max_results, topic="general")
    result = search.invoke({"query": query})
    return _format_search_result(result)


def _format_search_result(result: object) -> str:
    if isinstance(result, str):
        return result

    if not isinstance(result, dict):
        return json.dumps(result, ensure_ascii=False, default=str)

    lines: list[str] = []
    answer = result.get("answer")
    if answer:
        lines.append(f"Resumen: {answer}")

    results = result.get("results") or []
    for index, item in enumerate(results, start=1):
        title = item.get("title", "Sin título")
        url = item.get("url", "")
        content = item.get("content", "")
        lines.append(f"{index}. {title}\n   URL: {url}\n   {content}")

    if not lines:
        return "No se encontraron resultados para la consulta."

    return "\n\n".join(lines)


RESEARCH_TOOLS = [web_search]
