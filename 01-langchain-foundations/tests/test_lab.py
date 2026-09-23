from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from stage_b_prompt import translation_prompt
from tools import ADD_EXECUTIONS, add, get_current_date

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
