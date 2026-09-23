"""Checks for MCP stages introduced so far."""

import asyncio
import sys
from pathlib import Path

import pytest
from mcp import Client

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from direct_tool import add  # noqa: E402
from mcp_server import mcp  # noqa: E402
from stage_b_server import run as server_run  # noqa: E402
from raw_client import inspect_client  # noqa: E402
from stage_d_stdio import run as stdio_run  # noqa: E402
from stage_e_http import run as http_run  # noqa: E402
from stage_f_mcp_adapter import run as adapter_run  # noqa: E402
from stage_g_agent_mcp import run as agent_run  # noqa: E402
from stage_h_compare import run as comparison_run  # noqa: E402

def test_direct_add() -> None:
    assert add(2, 3) == 5
    with pytest.raises(TypeError):
        add("abc", 3)


def test_server_tool_schema_resource_prompt() -> None:
    asyncio.run(server_run())


def test_raw_mcp_discovery_and_call() -> None:
    async def check() -> None:
        async with Client(mcp) as client:
            evidence = await inspect_client(client, label="TEST_RAW")
        assert evidence["add"] == {"result": 5}

    asyncio.run(check())


def test_stdio_discovery_and_logging() -> None:
    asyncio.run(stdio_run())


def test_http_discovery_and_shutdown() -> None:
    asyncio.run(http_run())


def test_mcp_adapter_tool_conversion() -> None:
    asyncio.run(adapter_run())


def test_agent_calls_mcp_tool() -> None:
    asyncio.run(agent_run())


def test_direct_adapter_mcp_comparison() -> None:
    asyncio.run(comparison_run())
