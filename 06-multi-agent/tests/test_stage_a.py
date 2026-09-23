import json

from tools import CALLS, find_demo_doctors, get_history_records, search_demo_guideline
from workers import SPECS


def test_record_tool_uses_only_synthetic_data():
    CALLS.clear()
    payload = json.loads(get_history_records.invoke({"user_id": "user_123"}))
    assert payload["status"] == "OK" and len(payload["records"]) == 2
    assert CALLS == [("get_history_records", "user_123")]


def test_guideline_and_doctor_tools():
    guide = json.loads(search_demo_guideline.invoke({"query": "general note"}))
    doctors = json.loads(find_demo_doctors.invoke({"specialty": "general directory"}))
    assert guide["status"] == "OK" and "fictional" in guide["text"]
    assert doctors["status"] == "OK" and len(doctors["doctors"]) == 2


def test_worker_tool_sets_are_distinct():
    assert {kind: spec[0].name for kind, spec in SPECS.items()} == {
        "record": "get_history_records",
        "guideline": "search_demo_guideline",
        "doctor": "find_demo_doctors",
    }
