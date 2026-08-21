"""Nodo de validación: rúbrica previa al cierre del flujo."""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from llm import get_llm
from state import OrchestratorState

VALIDATION_SYSTEM_PROMPT = """Sos el nodo de validación del orquestador multi-agente.

Evaluá si los aportes de research_agent y analyst_agent son suficientes
para responder la consulta del usuario antes de permitir FINISH.

Rúbrica (todas deben cumplirse para passed=true):
1. research_findings no está vacío y es relevante a la consulta
2. analysis_result no está vacío y se basa en esos hallazgos
3. En conjunto permiten redactar una respuesta útil a la consulta

Si falla:
- Indicá qué falta en feedback
- Sugerí refine_target: research_agent | analyst_agent
"""


class ValidationResult(BaseModel):
    """Resultado estructurado de la rúbrica de validación."""

    passed: bool = Field(description="True solo si la rúbrica se cumple por completo")
    feedback: str = Field(
        description="Qué falta o hay que refinar; vacío si passed=true"
    )
    refine_target: Literal["research_agent", "analyst_agent", "none"] = Field(
        description="A quién reenviar si falla; none si passed=true"
    )
    reasoning: str = Field(description="Justificación breve de la evaluación")


def validation_agent_node(state: OrchestratorState) -> dict:
    """Valida hallazgos + análisis con rúbrica estructurada.

    Solo recibe consulta, research_findings y analysis_result para evitar
    contaminación con el historial completo.
    """
    user_query = (state.get("user_query") or "").strip()
    research_findings = (state.get("research_findings") or "").strip()
    analysis_result = (state.get("analysis_result") or "").strip()
    step_count = int(state.get("step_count") or 0)

    # Guardas deterministas antes del LLM
    if not research_findings:
        return _reject(
            step_count=step_count,
            feedback="Faltan research_findings. El agente de investigación debe buscar información.",
            refine_target="research_agent",
            reasoning="research_findings vacío",
        )

    if not analysis_result:
        return _reject(
            step_count=step_count,
            feedback="Falta analysis_result. El analista debe procesar los hallazgos.",
            refine_target="analyst_agent",
            reasoning="analysis_result vacío",
        )

    snapshot = (
        f"Consulta del usuario:\n{user_query or 'N/A'}\n\n"
        f"Hallazgos de investigación:\n{research_findings}\n\n"
        f"Resultado de análisis:\n{analysis_result}"
    )

    llm = get_llm().with_structured_output(ValidationResult)
    result = llm.invoke(
        [
            SystemMessage(content=VALIDATION_SYSTEM_PROMPT),
            HumanMessage(content=snapshot),
        ]
    )

    if not isinstance(result, ValidationResult):
        return _reject(
            step_count=step_count,
            feedback="La validación no pudo producir un resultado estructurado. Reintentá el análisis.",
            refine_target="analyst_agent",
            reasoning="salida de validación inválida",
        )

    if result.passed:
        feedback = ""
        refine_note = "none"
        passed = True
    else:
        feedback = (result.feedback or "Output insuficiente según la rúbrica.").strip()
        refine_note = (
            result.refine_target
            if result.refine_target in ("research_agent", "analyst_agent")
            else "analyst_agent"
        )
        passed = False

    summary = (
        f"Validation -> {'PASS' if passed else 'FAIL'}. {result.reasoning}"
        + (f" | refine: {refine_note}" if not passed else "")
    )

    return {
        "validation_passed": passed,
        "validation_feedback": feedback,
        "messages": [AIMessage(content=summary, name="validation_agent")],
        "step_count": step_count + 1,
    }


def _reject(
    *,
    step_count: int,
    feedback: str,
    refine_target: str,
    reasoning: str,
) -> dict:
    return {
        "validation_passed": False,
        "validation_feedback": feedback,
        "messages": [
            AIMessage(
                content=(
                    f"Validation -> FAIL. {reasoning} | refine: {refine_target}"
                ),
                name="validation_agent",
            )
        ],
        "step_count": step_count + 1,
    }
