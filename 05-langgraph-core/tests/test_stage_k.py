from stage_k_final_graph import build_graph, initial_state


def test_final_fast_and_fanout_paths():
    graph = build_graph()
    assert graph.invoke(initial_state(" Hello "))["output"] == "fast:hello"
    result = graph.invoke(initial_state(" A, B, C "))
    assert result["output"] == "processed:a | processed:b | processed:c"
    assert set(result["results"]) == {"processed:a", "processed:b", "processed:c"}


def test_final_stream_and_mermaid():
    graph = build_graph()
    updates = list(graph.stream(initial_state(" X, Y "), stream_mode="updates"))
    assert updates[-1]["finalize"]["output"] == "processed:x | processed:y"
    diagram = graph.get_graph().draw_mermaid()
    assert all(node in diagram for node in ("normalize", "worker", "finalize"))
