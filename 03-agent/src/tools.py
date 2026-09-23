"""Small deterministic tools for the Agent Harness lessons."""

from datetime import date

from langchain_core.tools import tool


ADD_EXECUTIONS: list[tuple[int, int]] = []
DATE_EXECUTIONS: list[str] = []


@tool
def add(a: int, b: int) -> int:
    """Add two integers and return their sum."""
    ADD_EXECUTIONS.append((a, b))
    return a + b


@tool
def get_current_date() -> str:
    """Return today's local calendar date in ISO YYYY-MM-DD format."""
    value = date.today().isoformat()
    DATE_EXECUTIONS.append(value)
    return value


@tool(return_direct=True)
def echo_direct(text: str) -> str:
    """Return the given text directly without another model turn."""
    return text
