"""Stage I: explicit protocol failures and a simulated approval boundary."""

import asyncio

from mcp import Client
from mcp.server import MCPServer

from mcp_server import mcp
from raw_http_client import free_loopback_port
from raw_stdio_client import stdio_params
from stage_d_stdio import run as run_stdio


DELETE_ATTEMPTS: list[str] = []
security_server = MCPServer("security-example")


@security_server.tool()
def delete_resource(resource_id: str) -> str:
    """Simulate a sensitive deletion; no file, database, or service is touched."""
    DELETE_ATTEMPTS.append(resource_id)
    return f"SIMULATED delete: {resource_id}"


async def expected_tool_failure(name: str, args: dict) -> str:
    async with Client(mcp) as client:
        try:
            result = await client.call_tool(name, args)
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"
    if result.is_error:
        return str(result.content)
    raise AssertionError(f"{name} unexpectedly succeeded")


async def unavailable_server() -> str:
    port = free_loopback_port()
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        async with asyncio.timeout(5):
            async with Client(url, read_timeout_seconds=2) as client:
                await client.list_tools()
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    raise AssertionError("Unavailable server unexpectedly connected")


async def approval_gate(approved: bool, resource_id: str) -> str:
    """Application policy sits before MCP tool invocation."""
    if not approved:
        return "REJECTED BY HUMAN POLICY"
    async with Client(security_server) as client:
        result = await client.call_tool("delete_resource", {"resource_id": resource_id})
    assert not result.is_error
    return str(result.structured_content)


async def run() -> None:
    unknown = await expected_tool_failure("no_such_tool", {})
    invalid = await expected_tool_failure("add", {"a": "abc", "b": 3})
    unavailable = await unavailable_server()
    print(f"UNKNOWN_TOOL_ERROR={unknown[:300]}")
    print(f"INVALID_ARGUMENT_ERROR={invalid[:300]}")
    print(f"SERVER_UNAVAILABLE_ERROR={unavailable[:300]}")
    assert unknown and invalid and unavailable
    print("UNKNOWN_TOOL=PASS")
    print("INVALID_ARGUMENTS=PASS")
    print("SERVER_UNAVAILABLE=PASS")

    env_names = set(stdio_params().env or {})
    assert "OPENAI_API_KEY" not in env_names and "AWS_SECRET_ACCESS_KEY" not in env_names
    await run_stdio()
    print("STDIO_LOGGING_SECURITY=PASS")

    rejected = await approval_gate(False, "teaching-item")
    assert rejected == "REJECTED BY HUMAN POLICY" and not DELETE_ATTEMPTS
    simulated = await approval_gate(True, "teaching-item")
    assert "SIMULATED delete" in simulated and DELETE_ATTEMPTS == ["teaching-item"]
    print(f"SENSITIVE_ACTION_REJECT={rejected}")
    print(f"SENSITIVE_ACTION_APPROVE={simulated}")
    print("SIMULATED_APPROVAL_BOUNDARY=PASS")


if __name__ == "__main__":
    asyncio.run(run())
