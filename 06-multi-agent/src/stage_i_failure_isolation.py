"""I: distinguish missing data from execution errors and preserve success."""

from subagent_tools import create_subagent_tools
from supervisor import build_supervisor, invoke_supervisor
from tools import CALLS
from workers import build_workers


QUERY = (
    "Use ask_record_agent for synthetic history records of user_123 and "
    "ask_doctor_agent for specialty simulate_failure. These are two different "
    "tasks. Report the record success and the directory execution error separately."
)


def run() -> None:
    CALLS.clear()
    events: list[dict] = []
    wrappers = create_subagent_tools(build_workers(), events)
    by_name = {item.name: item for item in wrappers}

    missing = by_name["ask_record_agent"].invoke({"task": "synthetic records for user_missing"})
    failed = by_name["ask_doctor_agent"].invoke({"task": "specialty simulate_failure"})
    assert missing == "NO_DATA: record"
    assert failed == "DOCTOR_AGENT_ERROR: RuntimeError"
    print(f"NO_DATA_RESULT={missing} EXECUTION_ERROR_RESULT={failed}")

    CALLS.clear()
    events.clear()
    agent = build_supervisor(wrappers, required_calls=2)
    result = invoke_supervisor(agent, QUERY)
    names = [call["name"] for call in result["calls"]]
    assert set(names) == {"ask_record_agent", "ask_doctor_agent"}, names
    assert {item[0] for item in CALLS} == {"get_history_records", "find_demo_doctors"}
    tool_outputs = [str(item.content) for item in result["tool_messages"]]
    print(f"OBSERVED_FAILURE_CALLS={result['calls']} INTERNAL={CALLS} OUTPUTS={tool_outputs} FINAL={result['final']}")
    assert any(output.startswith("SYNTHETIC RECORDS:") for output in tool_outputs)
    assert "DOCTOR_AGENT_ERROR: RuntimeError" in tool_outputs
    assert "2026" in result["final"] and "ERROR" in result["final"].upper(), result["final"]
    print(f"FAILURE_TOOL_CALLS={names} INTERNAL={CALLS}")
    print(f"FAILURE_TOOL_OUTPUTS={tool_outputs}")
    print(f"FAILURE_SUPERVISOR_FINAL={result['final']}")
    print("FAILURE_ISOLATION_PASS")


if __name__ == "__main__":
    run()
