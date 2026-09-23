"""Stage E: checkpointer state belongs to a thread, not the model."""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from model_factory import create_local_model


def message_texts(snapshot: object) -> list[str]:
    return [str(message.content) for message in snapshot.values["messages"]]


def run() -> None:
    agent = create_agent(
        model=create_local_model(max_tokens=128),
        tools=[],
        checkpointer=InMemorySaver(),
        system_prompt="Answer using only this conversation. If the user's name was never given, say you do not know it. /no_think",
    )
    config_a = {"configurable": {"thread_id": "03-memory-alice"}}
    config_b = {"configurable": {"thread_id": "03-memory-stranger"}}
    agent.invoke({"messages": [{"role": "user", "content": "My name is Alice. Remember it. /no_think"}]}, config_a)
    reply_a = agent.invoke({"messages": [{"role": "user", "content": "What is my name? /no_think"}]}, config_a)
    reply_b = agent.invoke({"messages": [{"role": "user", "content": "What is my name? /no_think"}]}, config_b)

    state_a = agent.get_state(config_a)
    state_b = agent.get_state(config_b)
    texts_a = message_texts(state_a)
    texts_b = message_texts(state_b)
    print(f"THREAD_A_MESSAGES={texts_a}")
    print(f"THREAD_B_MESSAGES={texts_b}")
    print(f"THREAD_A_REPLY={reply_a['messages'][-1].content}")
    print(f"THREAD_B_REPLY={reply_b['messages'][-1].content}")
    assert len(texts_a) == 4 and len(texts_b) == 2
    assert any("My name is Alice" in text for text in texts_a)
    assert all("Alice" not in text for text in texts_b)
    assert "Alice" in str(reply_a["messages"][-1].content)
    print("THREAD_MEMORY_ISOLATION=PASS")


if __name__ == "__main__":
    run()
