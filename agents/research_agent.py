"""Agente especialista de investigación / búsqueda."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from llm import get_llm
from state import OrchestratorState
from tools import RESEARCH_TOOLS

RESEARCH_SYSTEM_PROMPT = """Sos el agente de investigación del orquestador.

Tu único trabajo es buscar información externa relevante y devolver hallazgos claros.
Reglas:
- Usá siempre la herramienta web_search para respaldar tus conclusiones.
- Respondé en español, de forma concisa y estructurada.
- Incluí fuentes (títulos/URLs) cuando estén disponibles.
- No analices sentimiento ni valides esquemas: eso lo hace el analista.
- Si el feedback de validación indica huecos, priorizá cubrirlos.
"""


def build_research_agent():
    """Crea el agente ReAct de investigación con herramientas acotadas."""
    return create_react_agent(
        get_llm(),
        RESEARCH_TOOLS,
        prompt=RESEARCH_SYSTEM_PROMPT,
    )


def research_agent_node(state: OrchestratorState) -> dict:
    """Nodo LangGraph: investiga con contexto acotado y actualiza el estado.

    Solo recibe la consulta del usuario y, si existe, el feedback de validación
    para evitar contaminación con todo el historial de mensajes.
    """
    user_query = (state.get("user_query") or "").strip()
    if not user_query:
        user_query = _last_human_content(state.get("messages") or [])

    if not user_query:
        return {
            "research_findings": "Error: no hay consulta para investigar.",
            "step_count": int(state.get("step_count") or 0) + 1,
        }

    instruction = (
        "Investiga la siguiente consulta y resumí los hallazgos con fuentes:\n"
        f"{user_query}"
    )

    validation_feedback = (state.get("validation_feedback") or "").strip()
    if validation_feedback:
        instruction += (
            "\n\nFeedback de validación a considerar en esta nueva búsqueda:\n"
            f"{validation_feedback}"
        )

    agent = build_research_agent()
    result = agent.invoke({"messages": [HumanMessage(content=instruction)]})
    findings = _last_ai_content(result.get("messages") or [])

    return {
        "research_findings": findings,
        "validation_passed": False,
        "messages": [AIMessage(content=findings, name="research_agent")],
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
    return "No se obtuvieron hallazgos de investigación."


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