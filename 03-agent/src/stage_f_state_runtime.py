"""Stage F: ToolRuntime injects custom per-thread state into a tool."""

from langchain.agents import AgentState, create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AIMessage, ToolMessage

from model_factory import create_local_model


class CustomState(AgentState):
    user_id: str


SEEN_USER_IDS: list[str] = []


@tool
def get_user_info(runtime: ToolRuntime) -> str:
    """Return the current user's ID from agent state."""
    user_id = runtime.state["user_id"]
    SEEN_USER_IDS.append(user_id)
    return f"Current user ID: {user_id}"


def run() -> None:
    schema = get_user_info.tool_call_schema.model_json_schema()
    print(f"MODEL_VISIBLE_TOOL_SCHEMA={schema}")
    assert "runtime" not in schema.get("properties", {})
    agent = create_agent(
        model=create_local_model(),
        tools=[get_user_info],
        state_schema=CustomState,
        system_prompt="Use get_user_info to answer questions about the current user ID. /no_think",
    )
    result = agent.invoke(
        {
            "messages": [{"role": "user", "content": "Use get_user_info to find my current user ID. /no_think"}],
            "user_id": "user_123",
        }
    )
    messages = result["messages"]
    calls = [call for msg in messages if isinstance(msg, AIMessage) for call in msg.tool_calls]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    print(f"USER_ID_IN_AGENT_STATE={result['user_id']}")
    print(f"MODEL_TOOL_CALLS={calls}")
    print(f"TOOL_MESSAGES={[msg.content for msg in tool_messages]}")
    assert result["user_id"] == "user_123"
    assert SEEN_USER_IDS == ["user_123"]
    assert any(call["name"] == "get_user_info" for call in calls)
    assert any("user_123" in str(msg.content) for msg in tool_messages)
    print("STATE_TOOL_RUNTIME=PASS")


if __name__ == "__main__":
    run()
