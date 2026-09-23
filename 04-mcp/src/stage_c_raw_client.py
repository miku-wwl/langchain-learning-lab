"""Stage C: MCP discovery and invocation work without LangChain or LLM."""

import asyncio

from mcp import Client

from mcp_server import mcp
from raw_client import inspect_client


async def run() -> None:
    async with Client(mcp) as client:
        evidence = await inspect_client(client, label="IN_PROCESS")
    print(f"PROTOCOL_VERSION={evidence['protocol_version']}")
    print("MCP_DISCOVERY=PASS")
    print("MCP_CALL=PASS")
    print("MCP_RESOURCE=PASS")
    print("MCP_PROMPT=PASS")


if __name__ == "__main__":
    asyncio.run(run())
