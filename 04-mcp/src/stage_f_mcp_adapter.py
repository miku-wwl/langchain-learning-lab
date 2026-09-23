"""Stage F: the first-party adapter maps MCP tool schema to LangChain BaseTool."""

import asyncio

from langchain.mcp import MCPAdapter
from langchain_core.tools import BaseTool

from raw_stdio_client import SERVER


async def discover_adapter_tools() -> list[BaseTool]:
    async with MCPAdapter(SERVER) as adapter:
        tools = await adapter.list_tools()
        names = [tool.name for tool in tools]
        print(f"ADAPTER_DISCOVERED_TOOLS={names}")
        assert {"add", "get_course_stage"} <= set(names)
        add_tool = next(tool for tool in tools if tool.name == "add")
        assert isinstance(add_tool, BaseTool)
        assert add_tool.description
        schema_value = add_tool.tool_call_schema
        schema = schema_value.model_json_schema() if hasattr(schema_value, "model_json_schema") else schema_value
        print(f"LANGCHAIN_ADD_SCHEMA={schema}")
        assert {"a", "b"} <= set(schema["properties"])
        result = await add_tool.ainvoke({"a": 2, "b": 3})
        print(f"ADAPTER_ADD_RESULT={result}")
        assert "5" in str(result)
        return tools


async def run() -> None:
    await discover_adapter_tools()
    print("MCP_ADAPTER_DISCOVERY=PASS")
    print("MCP_TO_LANGCHAIN_TOOL=PASS")


if __name__ == "__main__":
    asyncio.run(run())
