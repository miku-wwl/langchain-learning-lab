from stage_d_runtime_context import build_graph


def test_runtime_context_and_config_do_not_join_state():
    observed = []
    result = build_graph(observed).invoke(
        {"message": ""}, context={"user_id": "u1"}, config={"recursion_limit": 10}
    )
    assert result == {"message": "hello u1"}
    assert observed == [{"user_id": "u1", "recursion_limit": 10}]
