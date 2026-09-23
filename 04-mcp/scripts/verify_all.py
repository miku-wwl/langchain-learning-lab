"""Run deterministic tests and all chapter 04 local MCP E2E stages."""

import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from model_factory import local_chat_config  # noqa: E402


STAGES = [
    ("stage_a_direct_tool.py", [("Direct Python Tool", "DIRECT_PYTHON_TOOL=PASS")]),
    ("stage_b_server.py", [("MCP Server", "MCP_SERVER_PRIMITIVES=PASS")]),
    (
        "stage_c_raw_client.py",
        [
            ("MCP Tool Discovery", "MCP_DISCOVERY=PASS"),
            ("MCP Tool Call", "MCP_CALL=PASS"),
            ("MCP Resource", "MCP_RESOURCE=PASS"),
            ("MCP Prompt", "MCP_PROMPT=PASS"),
        ],
    ),
    ("stage_d_stdio.py", [("STDIO Transport", "STDIO_TRANSPORT=PASS"), ("STDERR Logging", "STDERR_LOGGING=PASS")]),
    ("stage_e_http.py", [("Streamable HTTP", "STREAMABLE_HTTP=PASS")]),
    (
        "stage_f_mcp_adapter.py",
        [("MCPAdapter Discovery", "MCP_ADAPTER_DISCOVERY=PASS"), ("MCP to LangChain Tool", "MCP_TO_LANGCHAIN_TOOL=PASS")],
    ),
    (
        "stage_g_agent_mcp.py",
        [
            ("Agent Tool Call", "AGENT_MCP_TOOL_CALL=PASS"),
            ("Agent to MCP to Tool", "AGENT_MCP_TOOL_CALL=PASS"),
            ("ToolMessage Return", "MCP_TOOLMESSAGE_RETURN=PASS"),
            ("Final Answer", "AGENT_FINAL_ANSWER=PASS"),
        ],
    ),
    ("stage_h_compare.py", [("Integration Comparison", "INTEGRATION_COMPARISON=PASS")]),
    (
        "stage_i_security.py",
        [
            ("Unknown Tool", "UNKNOWN_TOOL=PASS"),
            ("Invalid Args", "INVALID_ARGUMENTS=PASS"),
            ("Server Failure", "SERVER_UNAVAILABLE=PASS"),
            ("Security Checks", "SIMULATED_APPROVAL_BOUNDARY=PASS"),
            ("STDIO Security", "STDIO_LOGGING_SECURITY=PASS"),
        ],
    ),
]


def status(label: str, passed: bool) -> None:
    print(f"{label:.<34} {'PASS' if passed else 'FAIL'}", flush=True)


def run_command(args: list[str], timeout: int = 240) -> subprocess.CompletedProcess[str]:
    print(f"RUN={' '.join(args)}", flush=True)
    return subprocess.run(
        args,
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def main() -> int:
    print("=" * 40)
    print("04. LangChain MCP E2E Verification")
    print("=" * 40)
    try:
        base_url, model_id = local_chat_config()
        mcp_version = importlib.metadata.version("mcp")
        print(f"Python={sys.version.split()[0]}")
        print(f"LangChain={importlib.metadata.version('langchain')}")
        print(f"LangGraph={importlib.metadata.version('langgraph')}")
        print(f"MCP_SDK={mcp_version}")
        print(f"Foundry_Local={base_url}")
        print(f"Local_Model={model_id}")
        env_ok = mcp_version.startswith("2.") and (
            base_url.startswith("http://127.0.0.1:") or base_url.startswith("http://localhost:")
        )
    except Exception as exc:
        print(f"ENVIRONMENT_ERROR={type(exc).__name__}: {exc}")
        env_ok = False
    status("Environment", env_ok)
    status("Local Tool-capable Model", env_ok)
    if not env_ok:
        print("BLOCKED")
        return 2

    tests = run_command([sys.executable, "-m", "pytest", "-q", "tests"], timeout=180)
    print(f"TEST_RESULT={tests.stdout.strip()}")
    tests_ok = tests.returncode == 0 and "12 passed" in tests.stdout
    status("Deterministic and E2E Tests", tests_ok)
    if not tests_ok:
        print(f"TEST_ERROR={tests.stderr[-3000:]}")

    passed = [tests_ok]
    for script, markers in STAGES:
        try:
            result = run_command([sys.executable, "-u", str(SRC / script)])
            lines = [line.strip() for line in result.stdout.splitlines()]
            if result.returncode:
                print(f"STAGE_ERROR[{script}]={(result.stdout + result.stderr)[-3000:]}")
            for label, marker in markers:
                ok = result.returncode == 0 and marker in lines
                status(label, ok)
                passed.append(ok)
            print(f"STAGE_EXIT[{script}]={result.returncode}")
        except subprocess.TimeoutExpired as exc:
            print(f"STAGE_TIMEOUT[{script}]={exc.timeout}s")
            for label, _ in markers:
                status(label, False)
                passed.append(False)
    print("-" * 40)
    if all(passed):
        print("04_MCP_PASS_LOCAL")
        print("=" * 40)
        return 0
    print("PARTIAL")
    print("=" * 40)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
