"""Helpers compartidos para tests unitarios."""

from unittest.mock import MagicMock


def make_structured_llm(return_value):
    """Simula get_llm().with_structured_output(...).invoke(...)."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    mock_structured.invoke.return_value = return_value
    return mock_llm


def base_state(**overrides):
    """Estado mínimo del orquestador para nodos."""
    state = {
        "messages": [],
        "user_query": "Que es LangGraph?",
        "next_agent": "research_agent",
        "research_findings": "",
        "analysis_result": "",
        "final_response": "",
        "task_completed": False,
        "step_count": 0,
        "validation_passed": False,
        "validation_feedback": "",
    }
    state.update(overrides)
    return state
