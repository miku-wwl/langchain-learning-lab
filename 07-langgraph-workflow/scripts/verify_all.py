"""Run every real local stage; print the final marker only when all pass."""

import importlib
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


STAGES = [
    ("stage_a_raw_streaming", ["Raw Stream Updates", "Raw Stream Values", "Raw Stream Custom"]),
    ("stage_b_event_streaming", ["Event Streaming"]),
    ("stage_c_checkpointer", ["Checkpointer", "Thread Isolation"]),
    ("stage_d_state_history", ["get_state", "get_state_history"]),
    ("stage_e_store", ["Checkpointer vs Store"]),
    ("stage_f_hitl", ["HITL Interrupt", "HITL Approve", "HITL Reject"]),
    ("stage_g_resume_semantics", ["Resume Re-execution", "Side-effect Boundary"]),
    ("stage_h_replay", ["Replay"]),
    ("stage_i_fork", ["Fork", "Original History Preserved"]),
    ("stage_j_multi_agent_runtime", ["Multi-Agent Streaming", "Multi-Agent Persistence"]),
    ("stage_k_multi_agent_hitl_time_travel", ["Multi-Agent HITL", "Multi-Agent Time Travel"]),
    ("stage_l_final_runtime", ["Final Runtime"]),
]


def main() -> None:
    print("=" * 49)
    print("07. LangGraph Workflow Runtime Verification")
    print("=" * 49)
    print(f"Python={sys.version.split()[0]} LangGraph={version('langgraph')} LangChain={version('langchain')}")
    print("Environment ........................ PASS")
    for module_name, labels in STAGES:
        try:
            importlib.import_module(module_name).run()
        except Exception as exc:
            print(f"{module_name} ................ FAILED: {type(exc).__name__}: {exc}")
            print("PARTIAL")
            raise
        for label in labels:
            print(f"{label:.<36} PASS")
    print("-" * 49)
    print("07_WORKFLOW_RUNTIME_PASS_LOCAL")
    print("=" * 49)


if __name__ == "__main__":
    main()
