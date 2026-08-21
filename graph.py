"""Grafo LangGraph del orquestador multi-agente jerárquico."""

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from agents import (
    analyst_agent_node,
    research_agent_node,
    route_after_supervisor,
    supervisor_node,
)
from state import OrchestratorState


def build_graph():
    """Construye y compila el grafo supervisor -> especialistas -> cierre."""
    workflow = StateGraph(OrchestratorState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("research_agent", research_agent_node)
    workflow.add_node("analyst_agent", analyst_agent_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "research_agent": "research_agent",
            "analyst_agent": "analyst_agent",
            "FINISH": END,
        },
    )
    workflow.add_edge("research_agent", "supervisor")
    workflow.add_edge("analyst_agent", "supervisor")

    return workflow.compile()


graph = build_graph()


def run_orchestrator(user_query: str) -> dict:
    """Ejecuta el orquestador con una consulta de usuario."""
    query = (user_query or "").strip()
    if not query:
        raise ValueError("user_query no puede estar vacía.")

    initial_state: OrchestratorState = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "next_agent": "research_agent",
        "research_findings": "",
        "analysis_result": "",
        "final_response": "",
        "task_completed": False,
        "step_count": 0,
        "validation_passed": False,
        "validation_feedback": "",
    }
    return graph.invoke(initial_state)


def get_graph_mermaid() -> str:
    """Devuelve el diagrama Mermaid de la topología compilada."""
    return graph.get_graph().draw_mermaid()
