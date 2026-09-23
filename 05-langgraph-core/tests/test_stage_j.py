from stage_j_streaming import build_graph


def test_stream_updates():
    assert list(build_graph().stream({"value": 1}, stream_mode="updates")) == [
        {"increment": {"value": 2}}, {"double": {"value": 4}}
    ]


def test_stream_values():
    values = list(build_graph().stream({"value": 1}, stream_mode="values"))
    assert [item["value"] for item in values] == [1, 2, 4]


def test_stream_custom_and_tasks():
    graph = build_graph()
    assert list(graph.stream({"value": 1}, stream_mode="custom")) == [
        {"progress": "doubling"}
    ]
    tasks = list(graph.stream({"value": 1}, stream_mode="tasks"))
    assert {task["name"] for task in tasks} == {"increment", "double"}
