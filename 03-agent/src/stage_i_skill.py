"""Stage I: expose a skill summary first, then load its full instructions on demand."""

from pathlib import Path
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain.tools import tool
from langchain_core.messages import AIMessage, ToolMessage

from model_factory import create_local_model


SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills"
SKILL_FILE = SKILL_ROOT / "ai_teacher" / "SKILL.md"
FULL_MARKER = "LESSON_PLAN_SEQUENCE"
LOAD_EVENTS: list[str] = []
MODEL_VIEWS: list[str] = []


def skill_summary(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("Missing SKILL.md frontmatter")
    frontmatter = text.split("---\n", 2)[1]
    fields = dict(line.split(":", 1) for line in frontmatter.splitlines() if ":" in line)
    return fields["name"].strip(), fields["description"].strip()


@tool
def load_skill(skill_name: Literal["ai_teacher"]) -> str:
    """Load the full instructions for a named skill when the skill summary matches a task."""
    if skill_name != "ai_teacher":
        return f"Unknown skill: {skill_name}"
    LOAD_EVENTS.append(skill_name)
    return SKILL_FILE.read_text(encoding="utf-8")


@wrap_model_call
def capture_model_view(request: ModelRequest, handler) -> ModelResponse:
    parts = [str(request.system_message.content) if request.system_message else ""]
    parts.extend(str(msg.content) for msg in request.messages)
    MODEL_VIEWS.append("\n".join(parts))
    if len(MODEL_VIEWS) == 1:
        request = request.override(tool_choice="required")
    return handler(request)


def run() -> None:
    name, description = skill_summary(SKILL_FILE)
    assert name == "ai_teacher"
    assert FULL_MARKER not in description
    agent = create_agent(
        model=create_local_model(alias="qwen2.5-0.5b"),
        tools=[load_skill],
        middleware=[capture_model_view],
        system_prompt=(
            "Available skill summaries:\n"
            f"- {name}: {description}\n"
            "If the user needs a lesson plan, call load_skill with skill_name='ai_teacher' first, "
            "then follow its full instructions."
        ),
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Make me a tiny AI lesson plan. Use the ai_teacher skill."}]}
    )
    messages = result["messages"]
    calls = [call for msg in messages if isinstance(msg, AIMessage) for call in msg.tool_calls]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    print(f"INITIAL_SUMMARY={name}: {description}")
    print(f"MODEL_TOOL_CALLS={calls}")
    print(f"LOAD_EVENTS={LOAD_EVENTS}")
    print(f"MODEL_VIEW_MARKER_FLAGS={[FULL_MARKER in view for view in MODEL_VIEWS]}")
    print(f"TOOL_CONTENT_MARKER_FLAGS={[FULL_MARKER in str(msg.content) for msg in tool_messages]}")
    assert LOAD_EVENTS == ["ai_teacher"]
    assert any(call["name"] == "load_skill" for call in calls)
    assert any(FULL_MARKER in str(msg.content) for msg in tool_messages)
    assert len(MODEL_VIEWS) >= 2
    assert FULL_MARKER not in MODEL_VIEWS[0]
    assert FULL_MARKER in MODEL_VIEWS[-1]
    print("SKILL_PROGRESSIVE_DISCLOSURE=PASS")


if __name__ == "__main__":
    run()
