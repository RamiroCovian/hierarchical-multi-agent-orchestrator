"""Nodo supervisor: routing, validación y cierre del flujo."""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from llm import get_llm
from state import NextAgent, OrchestratorState

DEFAULT_MAX_STEPS = 6

SUPERVISOR_SYSTEM_PROMPT = """Sos el supervisor de un orquestador multi-agente.

Dada la conversación/estado actual, ¿quién debe intervenir ahora o es momento de finalizar?

Nodos disponibles:
- research_agent: busca información externa
- analyst_agent: analiza hallazgos (sentimiento, puntos clave, validación)
- FINISH: cerrar con una respuesta final sintetizada

Rúbrica de validación antes de FINISH (todas deben cumplirse):
1. Hay research_findings no vacíos y relevantes a la consulta
2. Hay analysis_result no vacío basado en esos hallazgos
3. Podés redactar una respuesta final que responda la consulta

Flujo típico: research_agent → analyst_agent → FINISH.
Evítá bucles innecesarios. Si falta investigación → research_agent.
Si hay research pero falta análisis → analyst_agent.
Si ambos son suficientes → FINISH con final_response en español.
"""


class SupervisorDecision(BaseModel):
    """Decisión estructurada de routing del supervisor."""

    next_agent: NextAgent = Field(
        description="Nodo siguiente: research_agent, analyst_agent o FINISH"
    )
    reasoning: str = Field(description="Justificación breve de la decisión")
    validation_passed: bool = Field(
        description="True solo si la rúbrica permite finalizar"
    )
    validation_feedback: str = Field(
        default="",
        description="Qué falta o hay que refinar si no se puede finalizar",
    )
    final_response: str = Field(
        default="",
        description="Respuesta final al usuario solo si next_agent es FINISH",
    )


def supervisor_node(state: OrchestratorState) -> dict:
    """Decide el próximo agente, valida resultados o finaliza la tarea."""
    step_count = int(state.get("step_count") or 0)

    if step_count >= DEFAULT_MAX_STEPS:
        return _force_finish(
            state,
            reason="Se alcanzó el límite de pasos del supervisor.",
        )

    snapshot = _build_state_snapshot(state)
    llm = get_llm().with_structured_output(SupervisorDecision)
    decision = llm.invoke(
        [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=snapshot),
        ]
    )

    if not isinstance(decision, SupervisorDecision):
        return _force_finish(
            state,
            reason="El supervisor no pudo producir una decisión válida.",
        )

    next_agent = decision.next_agent
    if next_agent not in ("research_agent", "analyst_agent", "FINISH"):
        next_agent = "FINISH"

    if next_agent == "FINISH":
        final_response = (decision.final_response or "").strip()
        if not final_response:
            final_response = _fallback_final_response(state)

        return {
            "next_agent": "FINISH",
            "task_completed": True,
            "validation_passed": True,
            "validation_feedback": "",
            "final_response": final_response,
            "messages": [
                AIMessage(
                    content=f"Supervisor -> FINISH. {decision.reasoning}",
                    name="supervisor",
                )
            ],
            "step_count": step_count + 1,
        }

    return {
        "next_agent": next_agent,
        "task_completed": False,
        "validation_passed": bool(decision.validation_passed),
        "validation_feedback": (decision.validation_feedback or "").strip(),
        "messages": [
            AIMessage(
                content=f"Supervisor -> {next_agent}. {decision.reasoning}",
                name="supervisor",
            )
        ],
        "step_count": step_count + 1,
    }


def route_after_supervisor(
    state: OrchestratorState,
) -> Literal["research_agent", "analyst_agent", "FINISH"]:
    """Mapea la decisión del supervisor a nodos del grafo (aristas condicionales)."""
    next_agent = state.get("next_agent") or "FINISH"
    if next_agent in ("research_agent", "analyst_agent", "FINISH"):
        return next_agent
    return "FINISH"


def _build_state_snapshot(state: OrchestratorState) -> str:
    return (
        "Estado actual del orquestador:\n"
        f"- user_query: {state.get('user_query') or 'N/A'}\n"
        f"- research_findings: {state.get('research_findings') or 'N/A'}\n"
        f"- analysis_result: {state.get('analysis_result') or 'N/A'}\n"
        f"- validation_feedback: {state.get('validation_feedback') or 'N/A'}\n"
        f"- step_count: {int(state.get('step_count') or 0)}\n"
        f"- max_steps: {DEFAULT_MAX_STEPS}\n"
    )


def _force_finish(state: OrchestratorState, reason: str) -> dict:
    final_response = _fallback_final_response(state)
    return {
        "next_agent": "FINISH",
        "task_completed": True,
        "validation_passed": False,
        "validation_feedback": reason,
        "final_response": final_response,
        "messages": [
            AIMessage(
                content=f"Supervisor -> FINISH (forzado). {reason}",
                name="supervisor",
            )
        ],
        "step_count": int(state.get("step_count") or 0) + 1,
    }


def _fallback_final_response(state: OrchestratorState) -> str:
    analysis = (state.get("analysis_result") or "").strip()
    research = (state.get("research_findings") or "").strip()
    query = (state.get("user_query") or "").strip()

    if analysis:
        return analysis
    if research:
        return (
            f"Respuesta basada en investigación para '{query or 'la consulta'}':\n"
            f"{research}"
        )
    return (
        "No se pudo completar la tarea con suficiente evidencia. "
        f"Consulta: {query or 'N/A'}"
    )
