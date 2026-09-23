"""Stage E: let create_agent manage the model/tool/model cycle."""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage

from model_factory import create_local_model
from tools import ADD_EXECUTIONS, add


def run() -> None:
    agent = create_agent(
        model=create_local_model("qwen2.5-0.5b"),
        tools=[add],
        system_prompt="Use the add tool for arithmetic. After the tool result, answer briefly.",
    )
    before = len(ADD_EXECUTIONS)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Calculate 17 + 25 using add."}]},
        config={"recursion_limit": 8},
    )
    messages = result["messages"]
    calls = [call for m in messages if isinstance(m, AIMessage) for call in m.tool_calls]
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    print(f"AGENT_TOOL_CALLS={calls}")
    print(f"AGENT_TOOL_MESSAGES={[m.content for m in tool_messages]}")
    print(f"AGENT_FINAL={messages[-1].content}")
    assert any(call["name"] == "add" for call in calls)
    assert len(ADD_EXECUTIONS) > before, "Agent did not execute Python add"
    assert any(m.content == "42" for m in tool_messages)
    assert "42" in str(messages[-1].content)
    print("CREATE_AGENT_TOOL_LOOP=PASS")


if __name__ == "__main__":
    run()
