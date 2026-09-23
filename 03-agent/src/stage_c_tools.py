"""Stage C: reveal every message in a real create_agent tool loop."""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from model_factory import create_local_model
from tools import ADD_EXECUTIONS, DATE_EXECUTIONS, add, echo_direct, get_current_date


def inspect_loop(messages: list, tool_name: str) -> None:
    assert isinstance(messages[0], HumanMessage)
    calls = [call for msg in messages if isinstance(msg, AIMessage) for call in msg.tool_calls]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    print(f"{tool_name.upper()}_RAW_MESSAGES={[(type(msg).__name__, str(msg.content)[:500]) for msg in messages]}")
    assert any(call["name"] == tool_name for call in calls)
    assert any(msg.name == tool_name for msg in tool_messages)
    assert isinstance(messages[-1], AIMessage) and messages[-1].content
    print(f"{tool_name.upper()}_MESSAGE_TYPES={[type(msg).__name__ for msg in messages]}")
    print(f"{tool_name.upper()}_TOOL_CALLS={calls}")
    print(f"{tool_name.upper()}_TOOL_MESSAGES={[msg.content for msg in tool_messages]}")
    print(f"{tool_name.upper()}_FINAL={messages[-1].content}")


def run() -> None:
    agent = create_agent(
        model=create_local_model(),
        tools=[add, get_current_date],
        system_prompt="Use the provided tool for calculations and current dates. /no_think",
    )
    addition = agent.invoke(
        {"messages": [{"role": "user", "content": "Use add to calculate 17 + 25, then report its result. /no_think"}]}
    )
    inspect_loop(addition["messages"], "add")
    assert ADD_EXECUTIONS[-1] == (17, 25)
    assert any("42" in str(msg.content) for msg in addition["messages"] if isinstance(msg, ToolMessage))
    print("TOOL_CALLING_EXECUTION_LOOP=PASS")

    today = agent.invoke(
        {"messages": [{"role": "user", "content": "Use get_current_date to tell me today's date. /no_think"}]}
    )
    inspect_loop(today["messages"], "get_current_date")
    assert DATE_EXECUTIONS
    print("CURRENT_DATE_TOOL=PASS")

    direct_agent = create_agent(
        model=create_local_model(),
        tools=[echo_direct],
        system_prompt="Call echo_direct with the exact user text. /no_think",
    )
    direct = direct_agent.invoke(
        {"messages": [{"role": "user", "content": "Use echo_direct to return HELLO_DIRECT. /no_think"}]}
    )
    assert isinstance(direct["messages"][-1], ToolMessage)
    assert "HELLO_DIRECT" in str(direct["messages"][-1].content)
    print(f"RETURN_DIRECT_LAST_TYPE={type(direct['messages'][-1]).__name__}")
    print("RETURN_DIRECT=PASS")


if __name__ == "__main__":
    run()
