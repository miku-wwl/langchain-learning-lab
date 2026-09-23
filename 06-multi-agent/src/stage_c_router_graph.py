"""C: verify the graph invokes the selected worker rather than only routing."""

from router_graph import build_router_graph, initial_state
from tools import CALLS
from workers import build_workers


CASES = [
    ("Show synthetic history records for user_123", "record", "get_history_records"),
    ("Summarize the general demo guideline", "guideline", "search_demo_guideline"),
    ("List general demo doctors", "doctor", "find_demo_doctors"),
    ("What is the weather?", "refuse", ""),
]


def run() -> None:
    graph = build_router_graph(build_workers())
    for query, route, tool_name in CASES:
        CALLS.clear()
        result = graph.invoke(initial_state(query))
        assert result["route"] == route and result["worker_name"] == route
        assert result["worker_result"]
        if tool_name:
            assert result["worker_tool"] == tool_name
            assert len(CALLS) == 1 and CALLS[0][0] == tool_name
        else:
            assert not CALLS and result["worker_result"].startswith("REFUSED:")
        print(f"ROUTING_EVIDENCE={route} WORKER_TOOL={result['worker_tool']} CALLS={CALLS}")
        print(f"FINAL_STATE={result}")
    print("ROUTER_GRAPH_PASS")


if __name__ == "__main__":
    run()
