"""Deterministic checks for the stages introduced so far."""

import sys
from pathlib import Path

import pytest
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stage_d_tool_errors import divide, on_tool_error  # noqa: E402
from stage_f_state_runtime import CustomState, get_user_info  # noqa: E402
from tools import add, echo_direct, get_current_date  # noqa: E402

def test_tool_function_schema_and_execution() -> None:
    assert add.invoke({"a": 17, "b": 25}) == 42
    assert {"a", "b"} <= set(add.tool_call_schema.model_json_schema()["properties"])
    assert get_current_date.invoke({})
    assert echo_direct.return_direct is True


def test_tool_error_conversion_does_not_retry() -> None:
    with pytest.raises(ZeroDivisionError):
        divide.invoke({"a": 1, "b": 0})
    assert "ZeroDivisionError" in on_tool_error(ZeroDivisionError("b must not be zero"), object())


def test_thread_state_isolation_without_llm() -> None:
    builder = StateGraph(CustomState)
    builder.add_node("identity", lambda state: {})
    builder.set_entry_point("identity")
    builder.set_finish_point("identity")
    graph = builder.compile(checkpointer=InMemorySaver())
    a = {"configurable": {"thread_id": "unit-a"}}
    b = {"configurable": {"thread_id": "unit-b"}}
    graph.invoke({"messages": [HumanMessage(content="Alice")], "user_id": "alice"}, a)
    graph.invoke({"messages": [HumanMessage(content="What is my name?")]}, a)
    graph.invoke({"messages": [HumanMessage(content="What is my name?")], "user_id": "bob"}, b)
    state_a = graph.get_state(a).values
    state_b = graph.get_state(b).values
    assert state_a["user_id"] == "alice" and state_b["user_id"] == "bob"
    assert len(state_a["messages"]) == 2 and len(state_b["messages"]) == 1
    assert all("Alice" not in str(msg.content) for msg in state_b["messages"])


def test_custom_state_tool_runtime_injection() -> None:
    assert "runtime" not in get_user_info.tool_call_schema.model_json_schema().get("properties", {})
    runtime = ToolRuntime(
        state={"messages": [], "user_id": "user_123"},
        context=None,
        config={},
        stream_writer=lambda _: None,
        tool_call_id="unit-call",
        store=None,
    )
    assert "user_123" in get_user_info.func(runtime)
