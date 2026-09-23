"""Deterministic protocol checks plus one real local-model Agent E2E lane."""

import asyncio
import sys
from pathlib import Path

import pytest
from mcp import Client


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from direct_tool import add  # noqa: E402
from mcp_server import mcp  # noqa: E402
from raw_client import inspect_client  # noqa: E402
from stage_b_server import run as server_run  # noqa: E402
from stage_d_stdio import run as stdio_run  # noqa: E402
from stage_e_http import run as http_run  # noqa: E402
from stage_f_mcp_adapter import run as adapter_run  # noqa: E402
from stage_g_agent_mcp import run as agent_run  # noqa: E402
from stage_h_compare import run as comparison_run  # noqa: E402
from stage_i_security import (  # noqa: E402
    DELETE_ATTEMPTS,
    approval_gate,
    expected_tool_failure,
    unavailable_server,
)


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


def test_unknown_tool_failure() -> None:
    result = asyncio.run(expected_tool_failure("missing_tool", {}))
    assert "Unknown tool" in result


def test_invalid_argument_failure() -> None:
    result = asyncio.run(expected_tool_failure("add", {"a": "abc", "b": 3}))
    assert "validation error" in result.lower()


def test_unavailable_server_fails() -> None:
    result = asyncio.run(unavailable_server())
    assert "Exception" in result or "Error" in result


def test_simulated_approval_gate() -> None:
    async def check() -> None:
        DELETE_ATTEMPTS.clear()
        assert await approval_gate(False, "unit-item") == "REJECTED BY HUMAN POLICY"
        assert DELETE_ATTEMPTS == []
        assert "SIMULATED delete" in await approval_gate(True, "unit-item")
        assert DELETE_ATTEMPTS == ["unit-item"]

    asyncio.run(check())
