from stage_g_send import build_graph


def test_send_fanout_and_reducer_fanin():
    observed = []
    result = build_graph(observed).invoke({"subjects": ["A", "B", "C"], "results": []})
    assert set(observed) == {"A", "B", "C"} and len(observed) == 3
    assert set(result["results"]) == {"processed:A", "processed:B", "processed:C"}
    assert len(result["results"]) == 3
