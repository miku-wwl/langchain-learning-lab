"""Checks for MCP stages introduced so far."""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from direct_tool import add  # noqa: E402
from mcp_server import mcp  # noqa: E402
from stage_b_server import run as server_run  # noqa: E402

def test_direct_add() -> None:
    assert add(2, 3) == 5
    with pytest.raises(TypeError):
        add("abc", 3)


def test_server_tool_schema_resource_prompt() -> None:
    asyncio.run(server_run())
