"""Three independent create_agent specialists, each with one private tool."""

import json

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langchain_core.messages import AIMessage, ToolMessage

from model_factory import create_local_model
from tools import find_demo_doctors, get_history_records, search_demo_guideline


SPECS = {
    "record": (get_history_records, "synthetic record specialist; summarize only tool records"),
    "guideline": (search_demo_guideline, "fictional guideline-note specialist; summarize only tool text"),
    "doctor": (find_demo_doctors, "fictional doctor-directory specialist; list only tool entries"),
}


@wrap_model_call
def one_worker_tool_call(request, handler):
    """Make the worker's first model turn a real tool call, then let it answer."""
    used_tool = any(isinstance(message, ToolMessage) for message in request.messages)
    return handler(request.override(tool_choice="none" if used_tool else "required"))


def build_workers(*, alias: str = "phi-4-mini") -> dict:
    workers = {}
    for name, (worker_tool, role) in SPECS.items():
        workers[name] = create_agent(
            model=create_local_model(alias=alias), tools=[worker_tool],
            middleware=[one_worker_tool_call],
            system_prompt=(
                f"You are the {role}. Call your one tool exactly once before answering. "
                "Use only returned fictional data. No diagnosis, treatment or invented details. "
                "Summarize entries when present; if absent, state that no entry was found. "
                "Keep the final reply brief. /no_think"
            ),
        )
    return workers


def invoke_worker(workers: dict, kind: str, task: str) -> dict:
    result = workers[kind].invoke({"messages": [{"role": "user", "content": task}]})
    messages = result["messages"]
    tool_name = SPECS[kind][0].name
    calls = [call for msg in messages if isinstance(msg, AIMessage) for call in msg.tool_calls]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    assert any(call["name"] == tool_name for call in calls), (kind, calls)
    assert any(msg.name == tool_name for msg in tool_messages), (kind, tool_messages)
    assert isinstance(messages[-1], AIMessage) and str(messages[-1].content).strip()
    payload = json.loads(str(tool_messages[-1].content))
    if payload["status"] == "OK":
        if kind == "record":
            filtered = "SYNTHETIC RECORDS: " + "; ".join(payload["records"])
        elif kind == "guideline":
            filtered = "SYNTHETIC GUIDELINE NOTE: " + payload["text"]
        else:
            filtered = "SYNTHETIC DIRECTORY: " + "; ".join(
                f"{item['name']} ({item['specialty']})" for item in payload["doctors"]
            )
    else:
        filtered = f"NO_DATA: {kind}"
    return {
        "final": str(messages[-1].content), "filtered": filtered,
        "calls": calls, "tool_messages": tool_messages, "messages": messages,
    }
