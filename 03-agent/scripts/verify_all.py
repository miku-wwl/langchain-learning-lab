"""Verify every chapter 03 stage introduced in this commit."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ('stage_a_agent.py', ['CREATE_AGENT_CHAT=PASS']),
    ('stage_b_streaming_pii.py', ['STREAM_UPDATES=PASS', 'STREAM_MESSAGES=PASS', 'PII_BEFORE_MODEL=PASS']),
    ('stage_c_tools.py', ['TOOL_CALLING_EXECUTION_LOOP=PASS', 'CURRENT_DATE_TOOL=PASS', 'RETURN_DIRECT=PASS']),
    ('stage_d_tool_errors.py', ['TOOL_ERROR_MIDDLEWARE=PASS']),
    ('stage_e_memory.py', ['THREAD_MEMORY_ISOLATION=PASS']),
    ('stage_f_state_runtime.py', ['STATE_TOOL_RUNTIME=PASS']),
    ('stage_g_context.py', ['TRIM_VALID_TOOL_PAIR=PASS', 'SUMMARIZATION_MIDDLEWARE=PASS']),
    ('stage_h_hitl.py', ['HITL_SAFE_TOOL_NO_APPROVAL=PASS', 'HITL_APPROVE=PASS', 'HITL_REJECT=PASS']),
]


def main() -> int:
    if len(STAGES) >= 3:
        tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT, capture_output=True, text=True, timeout=120)
        print(tests.stdout.strip(), flush=True)
        if tests.returncode:
            print(tests.stderr[-1500:], flush=True)
            return 1
    for script, markers in STAGES:
        result = subprocess.run([sys.executable, "-u", str(ROOT / "src" / script)], cwd=ROOT, capture_output=True, text=True, timeout=240)
        lines = [line.strip() for line in result.stdout.splitlines()]
        passed = result.returncode == 0 and all(marker in lines for marker in markers)
        print(f"{script}: {'PASS' if passed else 'FAIL'}", flush=True)
        if not passed:
            print((result.stdout + result.stderr)[-2500:], flush=True)
            return 1
    print("STAGE_PREFIX_PASS_LOCAL", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
