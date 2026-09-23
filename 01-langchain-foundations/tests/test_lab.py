from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from stage_b_prompt import translation_prompt
from tools import ADD_EXECUTIONS, add, get_current_date
from langchain_core.messages import ToolMessage
from stage_d_manual_tool_loop import dispatch_tool_call

def test_prompt_inputs_are_required_and_rendered():
    template = translation_prompt()
    with pytest.raises(KeyError):
        template.invoke({"text": "hello"})
    rendered = template.invoke({"language": "Chinese", "text": "hello"})
    assert "Chinese" in rendered.messages[0].content
    assert rendered.messages[1].content == "hello"

def test_tools_execute_and_expose_schema():
    ADD_EXECUTIONS.clear()
    assert add.invoke({"a": 17, "b": 25}) == 42
    assert ADD_EXECUTIONS == [(17, 25)]
    assert set(add.args_schema.model_json_schema()["required"]) == {"a", "b"}
    assert len(get_current_date.invoke({})) == 10

def test_tool_dispatch_returns_matching_tool_message():
    ADD_EXECUTIONS.clear()
    call = {"name": "add", "args": {"a": 17, "b": 25}, "id": "test-call", "type": "tool_call"}
    message = dispatch_tool_call(call)
    assert isinstance(message, ToolMessage)
    assert message.content == "42" and message.tool_call_id == "test-call"
    assert ADD_EXECUTIONS == [(17, 25)]
