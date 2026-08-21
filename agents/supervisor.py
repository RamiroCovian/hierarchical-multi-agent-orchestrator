"""Nodo supervisor: routing y cierre del flujo."""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from llm import get_llm
from state import NextAgent, OrchestratorState

DEFAULT_MAX_STEPS = 8

SUPERVISOR_SYSTEM_PROMPT = """Sos el supervisor de un orquestador multi-agente.

Dada la conversación/estado actual, ¿quién debe intervenir ahora o es momento de finalizar?

Nodos disponibles:
- research_agent: busca información externa
- analyst_agent: analiza hallazgos (sentimiento, puntos clave, esquemas)
- validation_agent: aplica la rúbrica de calidad antes del cierre
- FINISH: cerrar con una respuesta final sintetizada

Reglas de enrutamiento:
1. Si falta investigación → research_agent
2. Si hay research pero falta análisis → analyst_agent
3. Si hay research y análisis pero validation_passed es false → validation_agent
4. Solo podés elegir FINISH si validation_passed es true
5. Si validation_feedback pide refinar, reenviá a research_agent o analyst_agent

Flujo típico: research_agent → analyst_agent → validation_agent → FINISH.
Evítá bucles innecesarios. Si finalizás, redactá final_response en español.
"""


class SupervisorDecision(BaseModel):
    """Decisión estructurada de routing del supervisor."""

    next_agent: NextAgent = Field(
        description=(
            "Nodo siguiente: research_agent, analyst_agent, "
            "validation_agent o FINISH"
        )
    )
    reasoning: str = Field(description="Justificación breve de la decisión")
    final_response: str = Field(
        default="",
        description="Respuesta final al usuario solo si next_agent es FINISH",
    )


def supervisor_node(state: OrchestratorState) -> dict:
    """Decide el próximo agente o finaliza la tarea tras validación."""
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
    allowed = ("research_agent", "analyst_agent", "validation_agent", "FINISH")
    if next_agent not in allowed:
        next_agent = "FINISH"

    # Gate duro: no cerrar sin validación aprobada
    validation_passed = bool(state.get("validation_passed"))
    if next_agent == "FINISH" and not validation_passed:
        has_research = bool((state.get("research_findings") or "").strip())
        has_analysis = bool((state.get("analysis_result") or "").strip())
        if has_research and has_analysis:
            next_agent = "validation_agent"
        elif has_research:
            next_agent = "analyst_agent"
        else:
            next_agent = "research_agent"

    if next_agent == "FINISH":
        final_response = (decision.final_response or "").strip()
        if not final_response:
            final_response = _fallback_final_response(state)

        return {
            "next_agent": "FINISH",
            "task_completed": True,
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
) -> Literal["research_agent", "analyst_agent", "validation_agent", "FINISH"]:
    """Mapea la decisión del supervisor a nodos del grafo (aristas condicionales)."""
    next_agent = state.get("next_agent") or "FINISH"
    if next_agent in (
        "research_agent",
        "analyst_agent",
        "validation_agent",
        "FINISH",
    ):
        return next_agent
    return "FINISH"


def _build_state_snapshot(state: OrchestratorState) -> str:
    return (
        "Estado actual del orquestador:\n"
        f"- user_query: {state.get('user_query') or 'N/A'}\n"
        f"- research_findings: {state.get('research_findings') or 'N/A'}\n"
        f"- analysis_result: {state.get('analysis_result') or 'N/A'}\n"
        f"- validation_passed: {bool(state.get('validation_passed'))}\n"
        f"- validation_feedback: {state.get('validation_feedback') or 'N/A'}\n"
        f"- step_count: {int(state.get('step_count') or 0)}\n"
        f"- max_steps: {DEFAULT_MAX_STEPS}\n"
    )


def _force_finish(state: OrchestratorState, reason: str) -> dict:
    final_response = _fallback_final_response(state)
    return {
        "next_agent": "FINISH",
        "task_completed": True,
        "validation_passed": bool(state.get("validation_passed")),
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
