"""Stage B: inspect registration of all three MCP primitives."""

import asyncio

from mcp_server import mcp


async def run() -> None:
    tools = await mcp.list_tools()
    resources = await mcp.list_resources()
    prompts = await mcp.list_prompts()
    names = {tool.name for tool in tools}
    resource_uris = {str(resource.uri) for resource in resources}
    prompt_names = {prompt.name for prompt in prompts}
    print(f"SERVER_TOOLS={sorted(names)}")
    print(f"SERVER_RESOURCES={sorted(resource_uris)}")
    print(f"SERVER_PROMPTS={sorted(prompt_names)}")
    assert {"add", "get_course_stage"} <= names
    assert "course://summary" in resource_uris
    assert "explain_mcp" in prompt_names
    add_tool = next(tool for tool in tools if tool.name == "add")
    print(f"ADD_SCHEMA={add_tool.input_schema}")
    assert {"a", "b"} <= set(add_tool.input_schema["properties"])
    print("MCP_SERVER_PRIMITIVES=PASS")


if __name__ == "__main__":
    asyncio.run(run())
