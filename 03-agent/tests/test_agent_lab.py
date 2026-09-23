"""Deterministic checks for the stages introduced so far."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tools import add, echo_direct, get_current_date  # noqa: E402

def test_tool_function_schema_and_execution() -> None:
    assert add.invoke({"a": 17, "b": 25}) == 42
    assert {"a", "b"} <= set(add.tool_call_schema.model_json_schema()["properties"])
    assert get_current_date.invoke({})
    assert echo_direct.return_direct is True
