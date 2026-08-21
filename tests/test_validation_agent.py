"""Tests del nodo de validación."""

from unittest.mock import patch

from agents.validation_agent import ValidationResult, validation_agent_node
from tests.helpers import base_state, make_structured_llm


def test_rejects_empty_research_without_llm():
    result = validation_agent_node(
        base_state(research_findings="", analysis_result="algo")
    )

    assert result["validation_passed"] is False
    assert "research_findings" in result["validation_feedback"]
    assert result["step_count"] == 1


def test_rejects_empty_analysis_without_llm():
    result = validation_agent_node(
        base_state(research_findings="hallazgos", analysis_result="")
    )

    assert result["validation_passed"] is False
    assert "analysis_result" in result["validation_feedback"]


@patch("agents.validation_agent.get_llm")
def test_passes_when_llm_approves(mock_get_llm):
    mock_get_llm.return_value = make_structured_llm(
        ValidationResult(
            passed=True,
            feedback="",
            refine_target="none",
            reasoning="Cumple la rubrica",
        )
    )
    state = base_state(
        research_findings="LangGraph es un framework de grafos",
        analysis_result="Util para orquestar agentes",
        step_count=3,
    )

    result = validation_agent_node(state)

    assert result["validation_passed"] is True
    assert result["validation_feedback"] == ""
    assert result["step_count"] == 4
    assert result["messages"][0].name == "validation_agent"
    assert "PASS" in result["messages"][0].content


@patch("agents.validation_agent.get_llm")
def test_fails_when_llm_rejects(mock_get_llm):
    mock_get_llm.return_value = make_structured_llm(
        ValidationResult(
            passed=False,
            feedback="El analisis no responde la consulta",
            refine_target="analyst_agent",
            reasoning="Analisis insuficiente",
        )
    )
    state = base_state(
        research_findings="Hallazgos",
        analysis_result="Analisis flojo",
    )

    result = validation_agent_node(state)

    assert result["validation_passed"] is False
    assert "no responde" in result["validation_feedback"]
    assert "FAIL" in result["messages"][0].content
