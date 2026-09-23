"""G: one supervisor request must use record and doctor subagents."""

from langchain_core.messages import AIMessage

from subagent_tools import create_subagent_tools
from supervisor import build_supervisor, invoke_supervisor
from tools import CALLS
from workers import build_workers


QUERY = (
    "Use ask_record_agent to summarize synthetic history records for user_123, "
    "and use ask_doctor_agent to list general synthetic doctors. "
    "This request needs BOTH different specialists. Report both results."
)


def run() -> None:
    CALLS.clear()
    events: list[dict] = []
    agent = build_supervisor(create_subagent_tools(build_workers(), events), required_calls=2)
    result = invoke_supervisor(agent, QUERY)
    names = [call["name"] for call in result["calls"]]
    print(f"OBSERVED_CALLS={names} INTERNAL={CALLS} TOOL_MESSAGES={[str(m.content) for m in result['tool_messages']]} OBSERVED_FINAL={result['final']}")
    assert set(names) == {"ask_record_agent", "ask_doctor_agent"}, names
    assert {item["internal_tool"] for item in events} == {"get_history_records", "find_demo_doctors"}
    assert {item[0] for item in CALLS} == {"get_history_records", "find_demo_doctors"}
    assert "Dr Demo" in result["final"] and ("2026" in result["final"] or "visit" in result["final"].lower())
    parallel = any(len(message.tool_calls) >= 2 for message in result["messages"] if isinstance(message, AIMessage))
    print(f"MULTI_DELEGATE_TOOL_CALLS={names} INTERNAL={CALLS}")
    print(f"MULTI_DELEGATE_FINAL={result['final']}")
    print("PARALLEL_DELEGATION_PASS" if parallel else "PARALLEL_DELEGATION_OPTIONAL_SEQUENTIAL")
    print("MULTI_DELEGATE_PASS")


if __name__ == "__main__":
    run()
