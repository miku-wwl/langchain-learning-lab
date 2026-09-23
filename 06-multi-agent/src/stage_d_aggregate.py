"""D: the worker result is not the graph's final user-facing response."""

from aggregate import aggregate_result
from router_graph import build_router_graph, initial_state
from tools import CALLS
from workers import build_workers


def run() -> None:
    CALLS.clear()
    graph = build_router_graph(build_workers(), aggregate_result)
    updates = list(graph.stream(initial_state("Show synthetic history records for user_123"), stream_mode="updates"))
    assert [next(iter(update)) for update in updates] == ["router", "record", "aggregate"]
    assert updates[-1]["aggregate"]["final_answer"].startswith("SYNTHETIC RECORD RESULT:")
    assert CALLS == [("get_history_records", "user_123")]
    print(f"AGGREGATE_UPDATES={updates}")
    print("AGGREGATE_PASS")


if __name__ == "__main__":
    run()
