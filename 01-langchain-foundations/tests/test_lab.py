from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from stage_b_prompt import translation_prompt

def test_prompt_inputs_are_required_and_rendered():
    template = translation_prompt()
    with pytest.raises(KeyError):
        template.invoke({"text": "hello"})
    rendered = template.invoke({"language": "Chinese", "text": "hello"})
    assert "Chinese" in rendered.messages[0].content
    assert rendered.messages[1].content == "hello"
