"""Esquema de estado compartido del orquestador multi-agente."""

from typing import Literal

from langgraph.graph import MessagesState

NextAgent = Literal[
    "research_agent",
    "analyst_agent",
    "validation_agent",
    "FINISH",
]


class OrchestratorState(MessagesState):
    """Estado compartido entre supervisor y agentes especialistas.

    Extiende ``MessagesState`` para conservar el historial con el reducer
    ``add_messages``. Los campos extra rastrean qué agente aportó qué
    información, evitan pérdida de contexto entre nodos y permiten al
    supervisor decidir el siguiente paso o finalizar.
    """

    # Consulta original (contexto estable para todos los nodos)
    user_query: str

    # Routing del supervisor → nodos del grafo o FINISH
    next_agent: NextAgent

    # Aportes por especialista (separados para no contaminar el historial)
    research_findings: str
    analysis_result: str

    # Síntesis / respuesta final hacia el usuario
    final_response: str

    # Control de completitud y anti-bucle del supervisor
    task_completed: bool
    step_count: int

    # Validación previa a END
    validation_passed: bool
    validation_feedback: str
