"""A: prove each specialist works before building a multi-agent coordinator."""

from tools import CALLS
from workers import build_workers, invoke_worker


TASKS = {
    "record": "Use get_history_records with user_id=user_123. Summarize fictional entries. /no_think",
    "guideline": "Use search_demo_guideline with query=general. Summarize fictional note. /no_think",
    "doctor": "Use find_demo_doctors with specialty=general. List fictional entries. /no_think",
}


def run() -> None:
    workers = build_workers()
    for kind, task in TASKS.items():
        CALLS.clear()
        result = invoke_worker(workers, kind, task)
        assert len(CALLS) == 1 and CALLS[0][0] == result["calls"][0]["name"]
        assert result["filtered"].startswith("SYNTHETIC ")
        print(f"{kind.upper()}_TOOL_CALLS={result['calls']}")
        print(f"{kind.upper()}_TOOL_MESSAGES={[str(m.content) for m in result['tool_messages']]}")
        print(f"{kind.upper()}_FINAL={result['final']}")
        print(f"{kind.upper()}_FILTERED={result['filtered']}")
        print(f"{kind.upper()}_WORKER_PASS")


if __name__ == "__main__":
    run()
