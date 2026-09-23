"""Start and always stop the trusted loopback MCP HTTP server for local checks."""

from contextlib import asynccontextmanager
import asyncio
import socket
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator

from raw_stdio_client import SERVER, stdio_params


def free_loopback_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def wait_for_server(process: subprocess.Popen, port: int, timeout: float = 15) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"MCP HTTP server exited early with {process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            await asyncio.sleep(0.1)
    raise TimeoutError("MCP HTTP server did not start")


@asynccontextmanager
async def running_http_server() -> AsyncIterator[tuple[str, int]]:
    port = free_loopback_port()
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stdout, tempfile.TemporaryFile(
        mode="w+t", encoding="utf-8"
    ) as stderr:
        process = subprocess.Popen(
            [sys.executable, str(SERVER), "--http", "--port", str(port)],
            cwd=SERVER.parent,
            env=stdio_params().env,
            stdout=stdout,
            stderr=stderr,
        )
        try:
            await wait_for_server(process, port)
            yield f"http://127.0.0.1:{port}/mcp", process.pid
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    await asyncio.to_thread(process.wait, 5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    await asyncio.to_thread(process.wait, 5)
            print(f"HTTP_SERVER_EXIT={process.returncode}")
            assert process.poll() is not None, "HTTP child process must be reaped"
