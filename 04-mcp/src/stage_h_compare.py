"""Stage H: compare three integration shapes using the same arithmetic capability."""

import asyncio

from mcp import Client

from direct_tool import add
from mcp_server import mcp


class CalculatorService:
    """In-process stand-in for a separately owned service in this teaching diagram."""

    def calculate(self, a: int, b: int) -> int:
        return add(a, b)


class DedicatedCalculatorAdapter:
    """One application-specific integration, with no discovery protocol."""

    def __init__(self, service: CalculatorService) -> None:
        self.service = service

    def add(self, a: int, b: int) -> int:
        return self.service.calculate(a, b)


async def run() -> None:
    direct = add(2, 3)
    dedicated = DedicatedCalculatorAdapter(CalculatorService()).add(2, 3)
    async with Client(mcp) as client:
        discovered = {tool.name for tool in (await client.list_tools()).tools}
        mcp_result = await client.call_tool("add", {"a": 2, "b": 3})
    protocol = mcp_result.structured_content["result"]
    print(f"DIRECT_PYTHON_TOOL={direct}")
    print(f"DEDICATED_ADAPTER={dedicated}")
    print(f"MCP_DISCOVERED_ADD={'add' in discovered} MCP_RESULT={protocol}")
    assert direct == dedicated == protocol == 5
    assert "add" in discovered
    print("INTEGRATION_COMPARISON=PASS")


if __name__ == "__main__":
    asyncio.run(run())
