"""Run every 06 stage against the actual local model, then deterministic tests."""

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ("a_workers", [
        ("Record Worker", "RECORD_WORKER_PASS"),
        ("Guideline Worker", "GUIDELINE_WORKER_PASS"),
        ("Doctor Worker", "DOCTOR_WORKER_PASS"),
    ]),
    ("b_router", [("Deterministic Router", "ROUTER_BASELINE_PASS")]),
    ("c_router_graph", [("Router Graph / Correct Worker / Refuse", "ROUTER_GRAPH_PASS")]),
    ("d_aggregate", [("Aggregate Node", "AGGREGATE_PASS")]),
    ("e_subagent_tools", [("Subagent Wrappers / Tool Namespace", "SUBAGENT_TOOL_PASS")]),
    ("f_supervisor", [("Supervisor / High-level + Internal Tool Calls", "SUPERVISOR_PASS")]),
    ("g_multi_delegate", [("Multi-Subagent Delegation", "MULTI_DELEGATE_PASS")]),
    ("h_context_isolation", [
        ("Context Isolation", "CONTEXT_ISOLATION_PASS"),
        ("Output Filtering", "OUTPUT_FILTERING_PASS"),
    ]),
    ("i_failure_isolation", [("Failure Isolation / No-Data vs Error", "FAILURE_ISOLATION_PASS")]),
    ("j_compare", [("Router vs Supervisor", "FINAL_COMPARISON_PASS")]),
]


def line(label: str, result: str) -> None:
    print(f"{label:.<45} {result}", flush=True)


def run(args: list[str], timeout: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)


def main() -> int:
    print("=" * 57)
    print("06. Multi-Agent E2E Verification")
    print("=" * 57, flush=True)
    versions = {name: importlib.metadata.version(name) for name in ("langchain", "langgraph", "langchain-openai", "pytest")}
    expected = {"langchain": "1.4.2", "langgraph": "1.2.12", "langchain-openai": "1.6.4", "pytest": "8.4.2"}
    environment_ok = sys.version_info >= (3, 13) and versions == expected
    line("Environment", "PASS" if environment_ok else "FAIL")
    print(f"Python={sys.version.split()[0]} versions={versions}", flush=True)

    status = run(["foundry", "server", "status", "--output", "json"], timeout=30)
    loaded = run(["foundry", "model", "list", "--loaded", "--output", "json"], timeout=30)
    model_ok = False
    if status.returncode == loaded.returncode == 0:
        server = json.loads(status.stdout)
        models = json.loads(loaded.stdout)["models"]
        model_ok = bool(server.get("running")) and any(
            item.get("alias") == "phi-4-mini" and item.get("cached")
            and item.get("supportsToolCalling") and item.get("device", "").lower() == "gpu"
            for item in models
        )
    line("Local Tool-capable Model", "PASS" if model_ok else "FAIL")
    all_ok = environment_ok and model_ok

    for stage, checks in STAGES:
        completed = run([sys.executable, "-u", str(ROOT / "src" / f"stage_{stage}.py")])
        stage_ok = completed.returncode == 0
        for label, marker in checks:
            passed = stage_ok and marker in completed.stdout
            line(label, "PASS" if passed else "FAIL")
            all_ok &= passed
        if stage == "g_multi_delegate":
            parallel = "PARALLEL_DELEGATION_PASS" in completed.stdout
            line("Parallel Delegation", "PASS" if parallel else "OPTIONAL (sequential)")
        if not stage_ok or not all(marker in completed.stdout for _, marker in checks):
            print(completed.stdout, flush=True)
            print(completed.stderr, file=sys.stderr, flush=True)

    tests = run([sys.executable, "-m", "pytest", "-q"], timeout=90)
    test_ok = tests.returncode == 0 and "20 passed" in tests.stdout
    line("Deterministic Tests", "PASS" if test_ok else "FAIL")
    print(tests.stdout.strip(), flush=True)
    if not test_ok:
        print(tests.stderr, file=sys.stderr, flush=True)
    all_ok &= test_ok

    line("Final Integrated Verification", "PASS" if all_ok else "FAIL")
    print("-" * 57)
    print("06_MULTI_AGENT_PASS_LOCAL" if all_ok else "06_MULTI_AGENT_PARTIAL")
    print("=" * 57)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
