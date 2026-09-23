"""Stage I: local stdio MCP server -> adapter -> LangChain agent."""

import asyncio
from pathlib import Path

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_core.messages import AIMessage, ToolMessage

from model_factory import create_local_model


async def run() -> None:
    server_script = Path(__file__).with_name("mcp_server.py")
    async with MCPAdapter(server_script) as adapter:
        tools = await adapter.list_tools()
        names = [tool.name for tool in tools]
        print(f"MCP_DISCOVERED_TOOLS={names}")
        assert "add" in names

        model = create_local_model()
        system_prompt = (
            "Use the MCP add tool for arithmetic. After its result, "
            "copy the exact number from the tool response into your final answer."
        )
        if "qwen3" in model.model_name.lower():
            system_prompt += " /no_think"
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
        )
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Use add to calculate 17 + 25."}]},
            config={"recursion_limit": 8},
        )

    messages = result["messages"]
    calls = [call for m in messages if isinstance(m, AIMessage) for call in m.tool_calls]
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    print(f"MCP_AGENT_TOOL_CALLS={calls}")
    print(f"MCP_TOOL_MESSAGES={[m.content for m in tool_messages]}")
    print(f"MCP_FINAL={messages[-1].content}")
    assert any(call["name"] == "add" for call in calls)
    assert any("42" in str(m.content) for m in tool_messages)
    assert "42" in str(messages[-1].content)
    print("LOCAL_MCP_AGENT_LOOP=PASS")


if __name__ == "__main__":
    asyncio.run(run())
