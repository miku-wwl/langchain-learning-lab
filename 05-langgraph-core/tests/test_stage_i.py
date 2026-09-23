from stage_i_subgraph import build_graph


def test_subgraph_output_is_merged_once():
    assert build_graph().invoke({"log": []}) == {"log": ["parent", "subgraph"]}
