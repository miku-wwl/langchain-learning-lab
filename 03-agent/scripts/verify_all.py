"""Run all chapter 03 local E2E examples and deterministic tests."""

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
    ("stage_a_agent.py", ["CREATE_AGENT_CHAT=PASS"]),
    ("stage_b_streaming_pii.py", ["STREAM_UPDATES=PASS", "STREAM_MESSAGES=PASS", "PII_BEFORE_MODEL=PASS"]),
    ("stage_c_tools.py", ["TOOL_CALLING_EXECUTION_LOOP=PASS", "CURRENT_DATE_TOOL=PASS", "RETURN_DIRECT=PASS"]),
    ("stage_d_tool_errors.py", ["TOOL_ERROR_MIDDLEWARE=PASS"]),
    ("stage_e_memory.py", ["THREAD_MEMORY_ISOLATION=PASS"]),
    ("stage_f_state_runtime.py", ["STATE_TOOL_RUNTIME=PASS"]),
    ("stage_g_context.py", ["TRIM_VALID_TOOL_PAIR=PASS", "SUMMARIZATION_MIDDLEWARE=PASS"]),
    ("stage_h_hitl.py", ["HITL_SAFE_TOOL_NO_APPROVAL=PASS", "HITL_APPROVE=PASS", "HITL_REJECT=PASS"]),
    ("stage_i_skill.py", ["SKILL_PROGRESSIVE_DISCLOSURE=PASS"]),
]


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


def print_status(label: str, passed: bool) -> None:
    print(f"{label:.<32} {'PASS' if passed else 'FAIL'}", flush=True)


def main() -> int:
    print("=" * 40)
    print("03. LangChain Agent E2E Verification")
    print("=" * 40)
    try:
        base_url, qwen3 = local_chat_config("qwen3-4b")
        _, qwen25 = local_chat_config("qwen2.5-0.5b")
        print(f"Python={sys.version.split()[0]}")
        print(f"LangChain={importlib.metadata.version('langchain')}")
        print(f"LangGraph={importlib.metadata.version('langgraph')}")
        print(f"Foundry_Local={base_url}")
        print(f"Models={qwen3}, {qwen25}")
        environment_ok = base_url.startswith("http://127.0.0.1:") or base_url.startswith("http://localhost:")
    except Exception as exc:
        print(f"ENVIRONMENT_ERROR={type(exc).__name__}: {exc}")
        environment_ok = False
    print_status("Environment", environment_ok)
    print_status("Local Tool-capable Model", environment_ok)
    if not environment_ok:
        print("BLOCKED")
        return 2

    results: dict[str, bool] = {}
    tests = run_command([sys.executable, "-m", "pytest", "-q", "tests"], timeout=120)
    print(f"TEST_RESULT={tests.stdout.strip()}")
    if tests.returncode:
        print(f"TEST_ERROR={tests.stderr[-2000:]}")
    results["Deterministic Tests"] = tests.returncode == 0 and "7 passed" in tests.stdout
    print_status("Deterministic Tests", results["Deterministic Tests"])

    for script, markers in STAGES:
        try:
            result = run_command([sys.executable, "-u", str(SRC / script)])
            if result.returncode:
                print(f"STAGE_ERROR[{script}]={(result.stdout + result.stderr)[-3000:]}")
            found = [line.strip() for line in result.stdout.splitlines()]
            for marker in markers:
                label = marker.split("=", 1)[0].replace("_", " ").title()
                passed = result.returncode == 0 and marker in found
                results[label] = passed
                print_status(label, passed)
            print(f"STAGE_EXIT[{script}]={result.returncode}")
        except subprocess.TimeoutExpired as exc:
            print(f"STAGE_TIMEOUT[{script}]={exc.timeout}s")
            for marker in markers:
                label = marker.split("=", 1)[0].replace("_", " ").title()
                results[label] = False
                print_status(label, False)

    print("-" * 40)
    if all(results.values()):
        print("03_AGENT_PASS_LOCAL")
        print("=" * 40)
        return 0
    print("PARTIAL")
    print("=" * 40)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
