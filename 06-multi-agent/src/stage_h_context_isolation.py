"""H: inspect the exact input and output crossing a subagent boundary."""

from subagent_tools import create_subagent_tools
from supervisor import build_supervisor, invoke_supervisor
from tools import CALLS
from workers import build_workers


CANARY = "UNRELATED_CONTEXT_CANARY_847"
QUERY = (
    "Use ask_record_agent for synthetic history records of user_123. "
    f"The main conversation also contains {CANARY}, a weather question, and "
    "unrelated directory discussion. Delegate only the record task."
)


def run() -> None:
    CALLS.clear()
    events: list[dict] = []
    agent = build_supervisor(create_subagent_tools(build_workers(), events))
    result = invoke_supervisor(agent, QUERY)
    assert [call["name"] for call in result["calls"]] == ["ask_record_agent"]
    assert len(events) == 1 and events[0]["kind"] == "record"
    event = events[0]
    assert CANARY not in event["worker_task"]
    assert "weather" not in event["worker_task"].lower()
    assert "directory" not in event["worker_task"].lower()
    assert "user_123" in event["worker_task"]
    assert "ToolMessage" in event["worker_message_types"]
    assert CALLS == [("get_history_records", "user_123")]
    print(f"SCOPED_WORKER_INPUT={event['worker_task']}")
    print("CONTEXT_ISOLATION_PASS")

    returned = str(result["tool_messages"][0].content)
    assert returned == event["returned"]
    assert returned.startswith("SYNTHETIC RECORDS:")
    assert CANARY not in returned
    assert "ToolMessage" not in returned and "tool_calls" not in returned
    assert "<think>" not in returned
    print(f"FILTERED_OUTPUT={returned}")
    print("OUTPUT_FILTERING_PASS")


if __name__ == "__main__":
    run()
