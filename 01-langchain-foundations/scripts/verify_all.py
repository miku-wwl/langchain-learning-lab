"""Run every local 01 stage and report one honest E2E result."""

import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from model_factory import local_model_config  # noqa: E402


STAGES = [
    ("Model Invoke / async / stream", "stage_a_model.py", "MODEL_INVOKE_ASYNC_STREAM=PASS"),
    ("Prompt Template", "stage_b_prompt.py", "PROMPT_TEMPLATE=PASS"),
    ("Tool Definition / Calling", "stage_c_tools.py", "BOUND_MODEL_PRODUCED_TOOL_CALL=PASS"),
    ("Manual Tool Loop", "stage_d_manual_tool_loop.py", "MANUAL_TOOL_LOOP=PASS"),
    ("create_agent", "stage_e_agent.py", "CREATE_AGENT_TOOL_LOOP=PASS"),
    ("Short-term Memory / Thread Isolation", "stage_f_memory.py", "SHORT_TERM_MEMORY_AND_THREAD_ISOLATION=PASS"),
    ("Middleware / Structured Output", "stage_g_extensions.py", "MIDDLEWARE_AND_STRUCTURED_OUTPUT=PASS"),
    ("LangGraph", "stage_h_graph.py", "LANGGRAPH_COMPILE_INVOKE=PASS"),
    ("MCP", "stage_i_mcp.py", "LOCAL_MCP_AGENT_LOOP=PASS"),
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 48)
    print("LangChain 01 E2E Verification")
    print("=" * 48)
    try:
        base_url, model_id = local_model_config()
        assert importlib.metadata.version("langchain") == "1.4.2"
        print(f"Environment .................. PASS")
        print(f"  Python {sys.version.split()[0]}; LangChain {importlib.metadata.version('langchain')}; LangGraph {importlib.metadata.version('langgraph')}")
        print(f"  Model {model_id}; endpoint {base_url}")
    except Exception as exc:
        print(f"Environment .................. BLOCKED: {exc}")
        print("PARTIAL")
        return 1

    failed = []
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["LANGSMITH_TRACING"] = "false"
    environment["LANGCHAIN_TRACING_V2"] = "false"
    for name, script, expected in STAGES:
        command = [sys.executable, str(LAB_ROOT / "src" / script)]
        try:
            result = subprocess.run(
                command,
                cwd=LAB_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            passed = result.returncode == 0 and expected in result.stdout
            print(f"{name:.<30} {'PASS' if passed else 'PARTIAL'}")
            for line in result.stdout.splitlines():
                if line.strip():
                    print(f"  {line}")
            if not passed:
                failed.append(name)
                for line in result.stderr.splitlines()[-12:]:
                    print(f"  ERROR: {line}")
        except subprocess.TimeoutExpired:
            failed.append(name)
            print(f"{name:.<30} PARTIAL (timeout after 180s)")

    print("LangSmith .................... OPTIONAL / NOT REQUIRED FOR LOCAL E2E")
    print("-" * 48)
    print("LOCAL_E2E_PASS" if not failed else f"PARTIAL: {', '.join(failed)}")
    print("=" * 48)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
