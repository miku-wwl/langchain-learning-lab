"""E: Supervisor tools hide worker-only tools while actually invoking workers."""

from router_graph import scoped_task
from subagent_tools import create_subagent_tools
from tools import CALLS
from workers import build_workers


INTERNAL = {"get_history_records", "search_demo_guideline", "find_demo_doctors"}
EXPECTED = {
    "record": ("ask_record_agent", "get_history_records"),
    "guideline": ("ask_guideline_agent", "search_demo_guideline"),
    "doctor": ("ask_doctor_agent", "find_demo_doctors"),
}


def run() -> None:
    events: list[dict] = []
    wrappers = create_subagent_tools(build_workers(), events)
    names = {item.name for item in wrappers}
    assert names == {item[0] for item in EXPECTED.values()}
    assert not names & INTERNAL
    for kind, (outer, inner) in EXPECTED.items():
        CALLS.clear()
        wrapper = next(item for item in wrappers if item.name == outer)
        result = wrapper.invoke({"task": scoped_task(kind, "user_123 general")})
        assert isinstance(result, str) and result
        assert CALLS and CALLS[-1][0] == inner
        assert events[-1]["kind"] == kind and events[-1]["internal_tool"] == inner
        print(f"SUBAGENT={outer} INTERNAL={CALLS[-1]} FINAL={result}")
    print(f"SUPERVISOR_TOOL_NAMESPACE={sorted(names)}")
    print("SUBAGENT_TOOL_PASS")


if __name__ == "__main__":
    run()
