"""Tests del nodo supervisor (gate FINISH y anti-bucle)."""

from unittest.mock import patch

from agents.supervisor import DEFAULT_MAX_STEPS, SupervisorDecision, supervisor_node
from tests.helpers import base_state, make_structured_llm


@patch("agents.supervisor.get_llm")
def test_blocks_finish_without_validation_when_data_ready(mock_get_llm):
    mock_get_llm.return_value = make_structured_llm(
        SupervisorDecision(
            next_agent="FINISH",
            reasoning="Quiere cerrar prematuramente",
            final_response="No deberia usarse",
        )
    )
    state = base_state(
        research_findings="Hallazgos sobre LangGraph",
        analysis_result="Analisis breve",
        validation_passed=False,
    )

    result = supervisor_node(state)

    assert result["next_agent"] == "validation_agent"
    assert result["task_completed"] is False
    assert "final_response" not in result


@patch("agents.supervisor.get_llm")
def test_blocks_finish_routes_to_research_if_empty(mock_get_llm):
    mock_get_llm.return_value = make_structured_llm(
        SupervisorDecision(
            next_agent="FINISH",
            reasoning="Cierre temprano",
            final_response="",
        )
    )

    result = supervisor_node(base_state(validation_passed=False))

    assert result["next_agent"] == "research_agent"


@patch("agents.supervisor.get_llm")
def test_blocks_finish_routes_to_analyst_if_only_research(mock_get_llm):
    mock_get_llm.return_value = make_structured_llm(
        SupervisorDecision(
            next_agent="FINISH",
            reasoning="Cierre temprano",
            final_response="",
        )
    )
    state = base_state(
        research_findings="Solo research",
        validation_passed=False,
    )

    result = supervisor_node(state)

    assert result["next_agent"] == "analyst_agent"


@patch("agents.supervisor.get_llm")
def test_allows_finish_when_validation_passed(mock_get_llm):
    mock_get_llm.return_value = make_structured_llm(
        SupervisorDecision(
            next_agent="FINISH",
            reasoning="Todo listo",
            final_response="LangGraph orquesta grafos multiagente.",
        )
    )
    state = base_state(
        research_findings="Hallazgos",
        analysis_result="Analisis",
        validation_passed=True,
    )

    result = supervisor_node(state)

    assert result["next_agent"] == "FINISH"
    assert result["task_completed"] is True
    assert "LangGraph" in result["final_response"]


def test_force_finish_on_max_steps():
    state = base_state(
        step_count=DEFAULT_MAX_STEPS,
        analysis_result="Respuesta de respaldo",
    )

    result = supervisor_node(state)

    assert result["next_agent"] == "FINISH"
    assert result["task_completed"] is True
    assert "límite de pasos" in result["validation_feedback"]
    assert result["final_response"] == "Respuesta de respaldo"
