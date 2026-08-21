"""Tests de topología del grafo compilado."""

from graph import build_graph, get_graph_mermaid


def test_graph_contains_expected_nodes():
    compiled = build_graph()
    nodes = set(compiled.get_graph().nodes)

    assert {
        "__start__",
        "supervisor",
        "research_agent",
        "analyst_agent",
        "validation_agent",
        "__end__",
    }.issubset(nodes)


def test_mermaid_mentions_validation_agent():
    mermaid = get_graph_mermaid()
    assert "validation_agent" in mermaid
    assert "supervisor" in mermaid
