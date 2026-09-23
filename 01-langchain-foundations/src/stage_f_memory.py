"""Stage F: checkpoint messages by thread and verify conversation isolation."""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from model_factory import create_local_model


def build_agent(checkpointer: InMemorySaver):
    return create_agent(
        model=create_local_model(),
        tools=[],
        system_prompt=(
            "Answer a user's name only from this conversation's messages. "
            "If the name is unknown, answer UNKNOWN. Be brief."
        ),
        checkpointer=checkpointer,
    )


def run() -> None:
    saver = InMemorySaver()
    agent = build_agent(saver)
    alice_thread = {"configurable": {"thread_id": "alice-thread"}}
    isolated_thread = {"configurable": {"thread_id": "new-thread"}}

    first = agent.invoke(
        {"messages": [{"role": "user", "content": "My name is Alice. Remember it."}]},
        config=alice_thread,
    )
    second = agent.invoke(
        {"messages": [{"role": "user", "content": "What is my name?"}]},
        config=alice_thread,
    )
    isolated = agent.invoke(
        {"messages": [{"role": "user", "content": "What is my name?"}]},
        config=isolated_thread,
    )
    alice_messages = agent.get_state(alice_thread).values["messages"]
    isolated_messages = agent.get_state(isolated_thread).values["messages"]

    print(f"TURN_1={first['messages'][-1].content}")
    print(f"TURN_2={second['messages'][-1].content}")
    print(f"NEW_THREAD={isolated['messages'][-1].content}")
    print(f"CHECKPOINT_MESSAGE_COUNTS={len(alice_messages)},{len(isolated_messages)}")
    assert "Alice" in str(second["messages"][-1].content)
    assert "Alice" not in str(isolated["messages"][-1].content)
    assert len(alice_messages) >= 4
    assert len(isolated_messages) == 2
    assert any("Alice" in str(m.content) for m in alice_messages)
    assert all("Alice" not in str(m.content) for m in isolated_messages)
    print("SHORT_TERM_MEMORY_AND_THREAD_ISOLATION=PASS")


if __name__ == "__main__":
    run()
