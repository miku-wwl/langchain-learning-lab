"""Verify every chapter 03 stage introduced in this commit."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ('stage_a_agent.py', ['CREATE_AGENT_CHAT=PASS']),
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
