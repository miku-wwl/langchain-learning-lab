from langgraph.graph.state import CompiledStateGraph

from stage_a_minimal_graph import build_graph


def test_minimal_graph_and_execution_order():
    order = []
    graph = build_graph(order)
    assert isinstance(graph, CompiledStateGraph)
    assert graph.invoke({"text": "START"}) == {"text": "START -> A -> B"}
    assert order == ["A", "B"]
