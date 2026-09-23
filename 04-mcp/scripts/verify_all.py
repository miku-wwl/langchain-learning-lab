"""Verify all chapter 04 stages introduced in this commit."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ('stage_a_direct_tool.py', ['DIRECT_PYTHON_TOOL=PASS']),
    ('stage_b_server.py', ['MCP_SERVER_PRIMITIVES=PASS']),
    ('stage_c_raw_client.py', ['MCP_DISCOVERY=PASS', 'MCP_CALL=PASS']),
    ('stage_d_stdio.py', ['STDIO_TRANSPORT=PASS']),
]


def main() -> int:
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT, capture_output=True, text=True, timeout=180)
    print(tests.stdout.strip(), flush=True)
    if tests.returncode:
        print(tests.stderr[-2000:], flush=True)
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
