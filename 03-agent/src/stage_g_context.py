"""Stage G: delete old messages, then separately summarize old messages."""

from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import SummarizationMiddleware, before_model
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from model_factory import create_local_model


TRIM_COUNTS: list[tuple[int, int]] = []


def keep_recent_valid_history(messages: list) -> list:
    """Keep the first message and recent four; avoid orphaning tool results."""
    kept = [messages[0], *messages[-4:]]
    call_ids = {call["id"] for msg in kept if isinstance(msg, AIMessage) for call in msg.tool_calls}
    result_ids = {msg.tool_call_id for msg in kept if isinstance(msg, ToolMessage)}
    if call_ids != result_ids:
        raise ValueError("Trim would break AI tool call / ToolMessage pairing")
    return kept


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state["messages"]
    if len(messages) <= 6:
        return None
    kept = keep_recent_valid_history(messages)
    TRIM_COUNTS.append((len(messages), len(kept)))
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *kept]}


def run_trim() -> None:
    history = [
        HumanMessage(content="Old greeting"),
        AIMessage(content="Hello"),
        HumanMessage(content="Old topic"),
        AIMessage(content="Understood"),
        HumanMessage(content="Please calculate this."),
        AIMessage(content="", tool_calls=[{"name": "add", "args": {"a": 1, "b": 2}, "id": "old-add"}]),
        ToolMessage(content="3", tool_call_id="old-add", name="add"),
        HumanMessage(content="What happened in our most recent calculation? /no_think"),
    ]
    agent = create_agent(
        model=create_local_model(max_tokens=128),
        tools=[],
        middleware=[trim_messages],
        system_prompt="Answer briefly using the available messages. /no_think",
    )
    result = agent.invoke({"messages": history})
    messages = result["messages"]
    print(f"TRIM_COUNTS_BEFORE_AFTER={TRIM_COUNTS}")
    print(f"TRIMMED_MESSAGE_TYPES={[type(msg).__name__ for msg in messages]}")
    print(f"TRIMMED_TOOL_IDS={[msg.tool_call_id for msg in messages if isinstance(msg, ToolMessage)]}")
    assert TRIM_COUNTS == [(8, 5)]
    assert len(messages) == 6  # Five retained messages plus the new model answer.
    assert any(isinstance(msg, ToolMessage) and msg.tool_call_id == "old-add" for msg in messages)
    assert any(isinstance(msg, AIMessage) and any(call["id"] == "old-add" for call in msg.tool_calls) for msg in messages)
    print("TRIM_VALID_TOOL_PAIR=PASS")


def run_summary() -> None:
    history = [
        HumanMessage(content="My favorite teaching topic is Python generators."),
        AIMessage(content="I will remember that topic."),
        HumanMessage(content="I prefer short examples."),
        AIMessage(content="I will use short examples."),
        HumanMessage(content="Please keep my preferences in mind."),
        AIMessage(content="Understood."),
        HumanMessage(content="What topic and style do I prefer? /no_think"),
    ]
    agent = create_agent(
        model=create_local_model(max_tokens=128),
        tools=[],
        middleware=[
            SummarizationMiddleware(
                model=create_local_model(max_tokens=160),
                trigger=("messages", 7),
                keep=("messages", 2),
                summary_prompt="Summarize the user's topic and style preferences in one short sentence. /no_think\n{messages}",
            )
        ],
        system_prompt="Answer using the summary and recent messages. /no_think",
    )
    result = agent.invoke({"messages": history})
    messages = result["messages"]
    print(f"SUMMARY_MESSAGE_TYPES={[type(msg).__name__ for msg in messages]}")
    print(f"SUMMARY_MESSAGES={[str(msg.content)[:300] for msg in messages]}")
    assert len(messages) < len(history) + 1
    assert any("generators" in str(msg.content).lower() for msg in messages)
    assert any("What topic and style" in str(msg.content) for msg in messages)
    print("SUMMARIZATION_MIDDLEWARE=PASS")


def run() -> None:
    run_trim()
    run_summary()


if __name__ == "__main__":
    run()
