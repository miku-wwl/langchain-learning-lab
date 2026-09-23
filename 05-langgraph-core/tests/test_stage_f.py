from stage_f_runtime_policies import build_cached_graph, build_handler_graph, build_retry_graph


def test_cache_hit_skips_node():
    calls = []
    graph = build_cached_graph(calls)
    assert graph.invoke({"number": 5}) == {"number": 10}
    assert graph.invoke({"number": 5}) == {"number": 10}
    assert calls == [5]


def test_retry_attempts_then_success():
    attempts = []
    assert build_retry_graph(attempts).invoke({"status": "pending"}) == {"status": "ok"}
    assert attempts == [1, 2, 3]


def test_error_handler_routes_to_fallback():
    attempts, errors = [], []
    result = build_handler_graph(attempts, errors).invoke({"status": "pending"})
    assert result == {"status": "fallback"}
    assert attempts == [1, 2]
    assert errors == ["always_fails:ConnectionError"]
