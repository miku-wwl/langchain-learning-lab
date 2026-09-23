"""One small MCPServer served over STDIO or loopback Streamable HTTP."""

import argparse
import os
import sys

from mcp.server import MCPServer

from direct_tool import add as direct_add


mcp = MCPServer("learning-demo")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return direct_add(a, b)


@mcp.tool()
def get_course_stage() -> str:
    """Return the current learning stage."""
    return "04. MCP"


@mcp.resource("course://summary")
def course_summary() -> str:
    """Describe the chapter in one sentence."""
    return "This chapter studies MCP clients, servers, transports, and LangChain integration."


@mcp.prompt()
def explain_mcp(audience: str = "beginner") -> str:
    """Return a reusable prompt for explaining MCP."""
    return f"Explain MCP to a {audience} using one simple architecture diagram."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Serve /mcp on loopback instead of STDIO")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.http:
        print(f"MCP_HTTP_STARTING=127.0.0.1:{args.port}", file=sys.stderr, flush=True)
        mcp.run(
            transport="streamable-http",
            host="127.0.0.1",
            port=args.port,
            json_response=True,
            stateless_http=True,
        )
    else:
        print(f"MCP_STDIO_STARTING pid={os.getpid()}", file=sys.stderr, flush=True)
        mcp.run()


if __name__ == "__main__":
    main()
