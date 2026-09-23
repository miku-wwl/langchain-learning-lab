from stage_b_state_boundaries import build_graph


def test_input_output_filtering_and_partial_updates():
    observed = []
    output = build_graph(observed).invoke({"user_input": "  langgraph  "})
    assert output == {"graph_output": "LANGGRAPH"}
    assert observed == [
        {"node": "prepare", "update": {"working_text": "langgraph"}},
        {"node": "process", "update": {"graph_output": "LANGGRAPH"}},
    ]
