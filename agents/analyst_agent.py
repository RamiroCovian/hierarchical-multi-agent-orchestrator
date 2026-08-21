"""Agente especialista de análisis / cómputo."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from llm import get_llm
from state import OrchestratorState
from tools import ANALYST_TOOLS

ANALYST_SYSTEM_PROMPT = """Sos el agente de análisis del orquestador.

Tu trabajo es procesar los hallazgos de investigación y producir un análisis claro.
Reglas:
- Usá analyze_sentiment, extract_key_points y/o validate_json_payload cuando aporten valor.
- Respondé en español, de forma concisa y estructurada.
- No busques en la web: eso lo hace el agente de investigación.
- Basate en los hallazgos recibidos y en la consulta del usuario.
- Si hay feedback de validación, corregí el análisis en esa dirección.
"""


def build_analyst_agent():
    """Crea el agente ReAct de análisis con herramientas acotadas."""
    return create_react_agent(
        get_llm(),
        ANALYST_TOOLS,
        prompt=ANALYST_SYSTEM_PROMPT,
    )


def analyst_agent_node(state: OrchestratorState) -> dict:
    """Nodo LangGraph: analiza con contexto acotado y actualiza el estado.

    Solo recibe la consulta, los hallazgos de investigación y, si existe,
    el feedback de validación — sin el historial completo de mensajes.
    """
    user_query = (state.get("user_query") or "").strip()
    if not user_query:
        user_query = _last_human_content(state.get("messages") or [])

    research_findings = (state.get("research_findings") or "").strip()
    if not user_query and not research_findings:
        return {
            "analysis_result": "Error: no hay consulta ni hallazgos para analizar.",
            "step_count": int(state.get("step_count") or 0) + 1,
        }

    instruction = (
        "Analizá la siguiente información y devolvé un informe estructurado.\n\n"
        f"Consulta del usuario:\n{user_query or 'N/A'}\n\n"
        f"Hallazgos de investigación:\n{research_findings or 'Sin hallazgos previos.'}"
    )

    validation_feedback = (state.get("validation_feedback") or "").strip()
    if validation_feedback:
        instruction += (
            "\n\nFeedback de validación a considerar en este nuevo análisis:\n"
            f"{validation_feedback}"
        )

    agent = build_analyst_agent()
    result = agent.invoke({"messages": [HumanMessage(content=instruction)]})
    analysis = _last_ai_content(result.get("messages") or [])

    return {
        "analysis_result": analysis,
        "messages": [AIMessage(content=analysis, name="analyst_agent")],
        "step_count": int(state.get("step_count") or 0) + 1,
    }


def _last_human_content(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
        if getattr(message, "type", None) == "human":
            return str(message.content)
    return ""


def _last_ai_content(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        is_ai = isinstance(message, AIMessage) or getattr(message, "type", None) == "ai"
        if is_ai:
            return _normalize_content(message.content)
    return "No se obtuvo resultado de análisis."


def _normalize_content(content: object) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
                continue
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
        return "\n".join(part for part in parts if part).strip()

    return str(content)
