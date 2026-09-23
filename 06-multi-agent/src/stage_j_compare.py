"""J: send the same single- and cross-domain requests through both patterns."""

from aggregate import aggregate_result
from router_graph import build_router_graph, initial_state
from stage_g_multi_delegate import QUERY as CROSS_QUERY
from subagent_tools import create_subagent_tools
from supervisor import build_supervisor, invoke_supervisor
from tools import CALLS
from workers import build_workers


SINGLE_QUERY = "Use ask_record_agent for synthetic history records of user_123."


def run() -> None:
    workers = build_workers()
    router = build_router_graph(workers, aggregate_result)
    wrappers = create_subagent_tools(workers)
    for label, query, required_calls in (
        ("single", SINGLE_QUERY, 1),
        ("cross", CROSS_QUERY, 2),
    ):
        CALLS.clear()
        routed = router.invoke(initial_state(query))
        router_calls = list(CALLS)
        CALLS.clear()
        supervised = invoke_supervisor(build_supervisor(wrappers, required_calls=required_calls), query)
        supervisor_calls = list(CALLS)
        names = [call["name"] for call in supervised["calls"]]
        assert routed["route"] == "record" and len(router_calls) == 1
        assert routed["final_answer"].startswith("SYNTHETIC RECORD RESULT:")
        if label == "single":
            assert names == ["ask_record_agent"]
            assert len(supervisor_calls) == 1
        else:
            assert set(names) == {"ask_record_agent", "ask_doctor_agent"}
            assert {item[0] for item in supervisor_calls} == {"get_history_records", "find_demo_doctors"}
            assert "Dr Demo" in supervised["final"] and "2026" in supervised["final"]
        print(f"CASE={label} ROUTER_ROUTE={routed['route']} ROUTER_TOOLS={router_calls}")
        print(f"CASE={label} SUPERVISOR_SUBAGENTS={names} WORKER_TOOLS={supervisor_calls}")
        print(f"CASE={label} ROUTER_FINAL={routed['final_answer']}")
        print(f"CASE={label} SUPERVISOR_FINAL={supervised['final']}")
    print("FINAL_COMPARISON_PASS")


if __name__ == "__main__":
    run()
