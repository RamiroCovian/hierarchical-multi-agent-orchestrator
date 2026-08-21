"""Tests de routing condicional del supervisor."""

from agents.supervisor import route_after_supervisor
from tests.helpers import base_state


def test_route_to_research_agent():
    assert route_after_supervisor(base_state(next_agent="research_agent")) == (
        "research_agent"
    )


def test_route_to_analyst_agent():
    assert route_after_supervisor(base_state(next_agent="analyst_agent")) == (
        "analyst_agent"
    )


def test_route_to_validation_agent():
    assert route_after_supervisor(base_state(next_agent="validation_agent")) == (
        "validation_agent"
    )


def test_route_to_finish():
    assert route_after_supervisor(base_state(next_agent="FINISH")) == "FINISH"


def test_route_unknown_defaults_to_finish():
    assert route_after_supervisor(base_state(next_agent="unknown")) == "FINISH"


def test_route_missing_next_agent_defaults_to_finish():
    state = base_state()
    del state["next_agent"]
    assert route_after_supervisor(state) == "FINISH"
