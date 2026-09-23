"""The capability exists before any MCP transport or agent."""


def add(a: int, b: int) -> int:
    """Add two integers."""
    if not isinstance(a, int) or isinstance(a, bool):
        raise TypeError("a must be an integer")
    if not isinstance(b, int) or isinstance(b, bool):
        raise TypeError("b must be an integer")
    return a + b
