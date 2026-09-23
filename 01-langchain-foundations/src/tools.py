"""Small deterministic tools shared by the local examples."""

from datetime import date

from langchain.tools import tool


ADD_EXECUTIONS: list[tuple[int, int]] = []


@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    ADD_EXECUTIONS.append((a, b))
    return a + b


@tool
def get_current_date() -> str:
    """Get today's local date in YYYY-MM-DD format."""
    return date.today().isoformat()
