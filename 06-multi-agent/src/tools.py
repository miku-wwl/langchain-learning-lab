"""Only fictional, read-only data lives behind these worker tools."""

import json
from pathlib import Path

from langchain.tools import tool


ROOT = Path(__file__).resolve().parents[1]
CALLS: list[tuple[str, str]] = []


def _resource(name: str) -> dict:
    return json.loads((ROOT / "resources" / name).read_text(encoding="utf-8"))


@tool
def get_history_records(user_id: str) -> str:
    """Look up fictional consultation entries for a demo user ID such as user_123."""
    CALLS.append(("get_history_records", user_id))
    records = _resource("synthetic_records.json").get(user_id)
    return json.dumps({"status": "OK", "records": records} if records else {"status": "NO_DATA"})


@tool
def search_demo_guideline(query: str) -> str:
    """Search a tiny local, fictional educational note by keyword such as general."""
    CALLS.append(("search_demo_guideline", query))
    key = "general" if "general" in query.lower() else query.lower()
    text = _resource("synthetic_guidelines.json").get(key)
    return json.dumps({"status": "OK", "text": text} if text else {"status": "NO_DATA"})


@tool
def find_demo_doctors(specialty: str) -> str:
    """Look up fictional directory entries by specialty such as general."""
    CALLS.append(("find_demo_doctors", specialty))
    if specialty == "simulate_failure":
        raise RuntimeError("simulated directory tool failure")
    key = "general" if "general" in specialty.lower() else specialty.lower()
    doctors = _resource("synthetic_doctors.json").get(key)
    return json.dumps({"status": "OK", "doctors": doctors} if doctors else {"status": "NO_DATA"})
