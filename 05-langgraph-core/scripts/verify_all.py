"""Execute every local stage in a fresh process and check the E2E gate."""

import importlib.metadata
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ("A", "minimal_graph", ("MINIMAL_GRAPH_PASS",)),
    ("B", "state_boundaries", ("STATE_BOUNDARY_PASS",)),
    ("C", "reducers", ("REDUCER_PASS",)),
    ("D", "runtime_context", ("RUNTIME_CONTEXT_PASS",)),
    ("E", "routing_loop", ("CONDITIONAL_ROUTING_PASS", "LOOP_PASS", "RECURSION_GUARD_PASS")),
    ("F", "runtime_policies", ("CACHE_PASS", "RETRY_PASS", "ERROR_HANDLER_PASS")),
    ("G", "send", ("SEND_FANOUT_PASS",)),
    ("H", "command", ("COMMAND_PASS",)),
    ("I", "subgraph", ("SUBGRAPH_PASS",)),
    ("J", "streaming", ("STREAM_UPDATES_PASS", "STREAM_VALUES_PASS", "STREAM_CUSTOM_PASS", "STREAM_TASKS_PASS")),
    ("K", "final_graph", ("FINAL_GRAPH_PASS",)),
]


def line(label: str, passed: bool) -> None:
    print(f"{label:.<37} {'PASS' if passed else 'FAIL'}", flush=True)


def execute(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=ROOT, text=True, capture_output=True, timeout=90, check=False
    )


def main() -> int:
    print("=" * 45)
    print("05. LangGraph Core E2E Verification")
    print("=" * 45, flush=True)
    versions = {
        name: importlib.metadata.version(name)
        for name in ("langgraph", "langchain-core", "pytest")
    }
    environment_ok = (
        sys.version_info >= (3, 13)
        and versions == {
            "langgraph": "1.2.12",
            "langchain-core": "1.6.4",
            "pytest": "8.4.2",
        }
    )
    print(f"Python={sys.version.split()[0]} packages={versions} runtime=pure Python")
    line("Environment", environment_ok)
    all_ok = environment_ok

    for letter, name, markers in STAGES:
        result = execute([sys.executable, "-u", str(ROOT / "src" / f"stage_{letter.lower()}_{name}.py")])
        passed = result.returncode == 0 and all(marker in result.stdout for marker in markers)
        line(f"Stage {letter} {name.replace('_', ' ')}", passed)
        if not passed:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        all_ok &= passed

    mermaid_path = ROOT / "docs" / "final-graph.mmd"
    mermaid_ok = mermaid_path.is_file() and all(
        token in mermaid_path.read_text(encoding="utf-8")
        for token in ("normalize", "worker", "finalize")
    )
    line("Mermaid Graph", mermaid_ok)
    all_ok &= mermaid_ok

    tests = execute([sys.executable, "-m", "pytest", "-q"])
    tests_ok = tests.returncode == 0 and "21 passed" in tests.stdout
    line("Deterministic tests", tests_ok)
    print(tests.stdout.strip())
    if not tests_ok:
        print(tests.stderr, file=sys.stderr)
    all_ok &= tests_ok

    print("-" * 45)
    print("05_LANGGRAPH_CORE_PASS_LOCAL" if all_ok else "05_LANGGRAPH_CORE_PARTIAL")
    print("=" * 45)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
