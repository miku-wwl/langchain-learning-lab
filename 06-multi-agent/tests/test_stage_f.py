import supervisor


def test_supervisor_is_create_agent_with_high_level_tools(monkeypatch):
    captured = {}
    monkeypatch.setattr(supervisor, "create_local_model", lambda: object())

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return "agent"

    monkeypatch.setattr(supervisor, "create_agent", fake_create_agent)
    wrappers = [type("ToolStub", (), {"name": name})() for name in ("ask_record_agent", "ask_guideline_agent", "ask_doctor_agent")]
    assert supervisor.build_supervisor(wrappers) == "agent"
    assert captured["tools"] is wrappers
    assert len(captured["middleware"]) == 1
    assert "get_history_records" not in [tool.name for tool in captured["tools"]]
