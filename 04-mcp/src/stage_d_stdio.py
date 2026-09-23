"""Stage D: a raw MCP Client launches its own STDIO Server process."""

import asyncio
import os
import re
import tempfile

from mcp import Client
from mcp.client.stdio import stdio_client

from raw_client import inspect_client
from raw_stdio_client import stdio_params


async def run() -> None:
    params = stdio_params()
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr:
        async with Client(stdio_client(params, errlog=stderr)) as client:
            evidence = await inspect_client(client, label="STDIO")
        stderr.seek(0)
        diagnostic = stderr.read()
    print(f"STDIO_SERVER_STDERR={diagnostic.strip()}")
    match = re.search(r"MCP_STDIO_STARTING pid=(\d+)", diagnostic)
    assert match is not None
    child_pid = int(match.group(1))
    assert child_pid != os.getpid()
    assert "add" in evidence["tools"] and "5" in str(evidence["add"])
    print(f"STDIO_CHILD_PID={child_pid} CLIENT_PID={os.getpid()}")
    print("STDIO_TRANSPORT=PASS")
    print("STDERR_LOGGING=PASS")


if __name__ == "__main__":
    asyncio.run(run())
