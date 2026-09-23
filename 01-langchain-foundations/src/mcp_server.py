"""A local MCP server launched over stdio by MCPAdapter."""

from fastmcp import FastMCP


server = FastMCP("langchain-01-local-tools")


@server.tool
def add(a: int, b: int) -> int:
    """Add two integers using this local MCP server."""
    return a + b


if __name__ == "__main__":
    server.run(transport="stdio")
