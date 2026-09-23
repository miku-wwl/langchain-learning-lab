import pytest

import router_graph


@pytest.mark.parametrize("query,expected,tool", [
    ("history user_123", "record", "get_history_records"),
    ("general guideline", "guideline", "search_demo_guideline"),
    ("general doctor", "doctor", "find_demo_doctors"),
])
def test_graph_selects_exact_worker(monkeypatch, query, expected, tool):
    invoked = []

    def fake_worker(workers, kind, task):
        invoked.append((kind, task))
        return {"calls": [{"name": tool}], "filtered": f"SYNTHETIC {kind}"}

    monkeypatch.setattr(router_graph, "invoke_worker", fake_worker)
    result = router_graph.build_router_graph({}).invoke(router_graph.initial_state(query))
    assert result["route"] == expected and result["worker_tool"] == tool
    assert len(invoked) == 1 and invoked[0][0] == expected


def test_graph_refuse_calls_no_worker(monkeypatch):
    monkeypatch.setattr(router_graph, "invoke_worker", lambda *_: pytest.fail("worker called"))
    result = router_graph.build_router_graph({}).invoke(router_graph.initial_state("weather"))
    assert result["route"] == "refuse" and result["worker_result"].startswith("REFUSED:")
