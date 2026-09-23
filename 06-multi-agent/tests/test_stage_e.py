from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import subagent_tools


def test_wrapper_schema_namespace_and_real_worker_boundary(monkeypatch):
    seen = []

    def fake_worker(workers, kind, task):
        seen.append((kind, task))
        return {
            "calls": [{"name": "get_history_records"}],
            "messages": [HumanMessage(content=task), AIMessage(content="call"), ToolMessage(content="{}", tool_call_id="1", name="get_history_records"), AIMessage(content="raw")],
            "filtered": "SYNTHETIC RECORDS: one",
        }

    monkeypatch.setattr(subagent_tools, "invoke_worker", fake_worker)
    events = []
    wrappers = subagent_tools.create_subagent_tools({}, events)
    names = {item.name for item in wrappers}
    assert names == {"ask_record_agent", "ask_guideline_agent", "ask_doctor_agent"}
    assert "get_history_records" not in names
    record = next(item for item in wrappers if item.name == "ask_record_agent")
    assert "task" in record.args_schema.model_fields
    assert record.invoke({"task": "user_123 and unrelated weather"}) == "SYNTHETIC RECORDS: one"
    assert seen[0][0] == "record" and "weather" not in seen[0][1]
    assert events[0]["internal_tool"] == "get_history_records"
