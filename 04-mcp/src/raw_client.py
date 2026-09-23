"""Transport-neutral raw MCP Client checks, without LangChain or an LLM."""

import json


async def inspect_client(client, *, label: str) -> dict:
    tools_result = await client.list_tools()
    tools = tools_result.tools
    names = [tool.name for tool in tools]
    print(f"{label}_DISCOVERED_TOOLS={names}")
    assert "add" in names and "get_course_stage" in names
    add_schema = next(tool.input_schema for tool in tools if tool.name == "add")
    assert {"a", "b"} <= set(add_schema["properties"])

    result = await client.call_tool("add", {"a": 2, "b": 3})
    print(f"{label}_ADD_STRUCTURED={result.structured_content}")
    assert not result.is_error
    assert "5" in json.dumps(result.structured_content)

    resources = await client.list_resources()
    resource_uris = [str(resource.uri) for resource in resources.resources]
    print(f"{label}_RESOURCES={resource_uris}")
    assert "course://summary" in resource_uris
    resource_result = await client.read_resource("course://summary")
    resource_text = str(resource_result.contents[0].text)
    assert "MCP clients" in resource_text

    prompts = await client.list_prompts()
    prompt_names = [prompt.name for prompt in prompts.prompts]
    print(f"{label}_PROMPTS={prompt_names}")
    assert "explain_mcp" in prompt_names
    prompt_result = await client.get_prompt("explain_mcp", {"audience": "beginner"})
    prompt_text = str(prompt_result.messages[0].content.text)
    assert "beginner" in prompt_text

    return {
        "tools": names,
        "add": result.structured_content,
        "resource": resource_text,
        "prompt": prompt_text,
        "protocol_version": client.protocol_version,
    }
