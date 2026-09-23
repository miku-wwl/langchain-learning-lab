import json

import pytest

import subagent_tools
from tools import CALLS, find_demo_doctors, get_history_records


def test_no_data_and_execution_error_are_distinct():
    assert json.loads(get_history_records.invoke({"user_id": "user_missing"})) == {"status": "NO_DATA"}
    with pytest.raises(RuntimeError, match="simulated directory"):
        find_demo_doctors.invoke({"specialty": "simulate_failure"})
    assert CALLS[-1] == ("find_demo_doctors", "simulate_failure")


def test_wrapper_contains_doctor_error(monkeypatch):
    def failed_worker(workers, kind, task):
        raise RuntimeError("simulated")

    monkeypatch.setattr(subagent_tools, "invoke_worker", failed_worker)
    doctor = subagent_tools.create_subagent_tools({})[2]
    assert doctor.invoke({"task": "simulate_failure"}) == "DOCTOR_AGENT_ERROR: RuntimeError"
