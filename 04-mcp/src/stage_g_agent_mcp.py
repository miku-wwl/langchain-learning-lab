"""Stage G: local model chooses an MCP-backed tool in a real Agent loop."""

import asyncio

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from model_factory import create_local_model, local_chat_config
from raw_stdio_client import SERVER


async def run() -> None:
    base_url, model_id = local_chat_config()
    print(f"LOCAL_MODEL={model_id} BASE_URL={base_url}")
    async with MCPAdapter(SERVER) as adapter:
        tools = await adapter.list_tools()
        names = [tool.name for tool in tools]
        print(f"AGENT_DISCOVERED_TOOLS={names}")
        assert "add" in names
        agent = create_agent(
            model=create_local_model(),
            tools=tools,
            system_prompt="Use the add tool for arithmetic, then answer briefly using its result. /no_think",
        )
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Use add to calculate 37 + 58, then report the result. /no_think"}]}
        )
    messages = result["messages"]
    calls = [call for msg in messages if isinstance(msg, AIMessage) for call in msg.tool_calls]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    print(f"AGENT_MESSAGE_TYPES={[type(msg).__name__ for msg in messages]}")
    print(f"AGENT_TOOL_CALLS={calls}")
    print(f"AGENT_TOOL_MESSAGES={[(msg.name, msg.content) for msg in tool_messages]}")
    print(f"AGENT_FINAL={messages[-1].content}")
    assert isinstance(messages[0], HumanMessage)
    assert any(call["name"] == "add" and call["args"] == {"a": 37, "b": 58} for call in calls)
    assert any(msg.name == "add" and "95" in str(msg.content) for msg in tool_messages)
    assert isinstance(messages[-1], AIMessage) and "95" in str(messages[-1].content)
    print("AGENT_MCP_TOOL_CALL=PASS")
    print("MCP_TOOLMESSAGE_RETURN=PASS")
    print("AGENT_FINAL_ANSWER=PASS")


if __name__ == "__main__":
    asyncio.run(run())
