"""Stage E: raw MCP Client connects via loopback Streamable HTTP."""

import asyncio
import os

from mcp import Client

from raw_client import inspect_client
from raw_http_client import running_http_server


async def run() -> None:
    async with running_http_server() as (url, server_pid):
        assert server_pid != os.getpid()
        print(f"MCP_HTTP_URL={url}")
        print(f"HTTP_SERVER_PID={server_pid} CLIENT_PID={os.getpid()}")
        async with Client(url, read_timeout_seconds=10) as client:
            evidence = await inspect_client(client, label="HTTP")
        assert "add" in evidence["tools"] and "5" in str(evidence["add"])
    print("STREAMABLE_HTTP=PASS")


if __name__ == "__main__":
    asyncio.run(run())
