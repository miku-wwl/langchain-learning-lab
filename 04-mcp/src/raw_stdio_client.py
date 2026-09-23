"""Explicit local subprocess parameters; only needed environment crosses the boundary."""

import os
from pathlib import Path
import sys

from mcp import StdioServerParameters


SERVER = Path(__file__).with_name("mcp_server.py").resolve()


def stdio_params() -> StdioServerParameters:
    allowed = ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")
    env = {name: os.environ[name] for name in allowed if name in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    return StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        cwd=str(SERVER.parent),
        env=env,
    )
