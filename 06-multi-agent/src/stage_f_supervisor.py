"""F: prove real supervisor -> subagent -> worker-tool -> supervisor loops."""

from subagent_tools import create_subagent_tools
from supervisor import build_supervisor, invoke_supervisor
from tools import CALLS
from workers import build_workers


CASES = [
    ("Use ask_record_agent for synthetic history records of user_123.", "ask_record_agent", "get_history_records", "2026"),
    ("Use ask_guideline_agent for the general synthetic guideline note.", "ask_guideline_agent", "search_demo_guideline", "fictional"),
    ("Use ask_doctor_agent for the general synthetic doctor directory.", "ask_doctor_agent", "find_demo_doctors", "Dr Demo"),
]


def run() -> None:
    events: list[dict] = []
    agent = build_supervisor(create_subagent_tools(build_workers(), events))
    for query, outer, inner, evidence in CASES:
        CALLS.clear()
        events.clear()
        result = invoke_supervisor(agent, query)
        names = [call["name"] for call in result["calls"]]
        assert names == [outer], (query, names)
        assert [message.name for message in result["tool_messages"]] == [outer]
        assert CALLS and CALLS[-1][0] == inner
        assert len(events) == 1
        assert events[0]["kind"] == outer.removeprefix("ask_").removesuffix("_agent")
        assert events[0]["internal_tool"] == inner
        assert evidence.lower() in result["final"].lower(), result["final"]
        print(f"SUPERVISOR_TOOL_CALLS={names} WORKER_INTERNAL_CALLS={CALLS}")
        print(f"SUPERVISOR_TOOL_MESSAGES={[str(m.content) for m in result['tool_messages']]}")
        print(f"SUPERVISOR_FINAL={result['final']}")
    print("SUPERVISOR_PASS")


if __name__ == "__main__":
    run()
