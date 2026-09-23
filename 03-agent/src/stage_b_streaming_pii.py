"""Stage B: inspect streaming events and the input seen after PII middleware."""

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, wrap_model_call

from model_factory import create_local_model


FAKE_EMAIL = "john.doe@example.com"
FAKE_CARD = "5105-1051-0510-5100"


def stream_agent() -> None:
    agent = create_agent(
        model=create_local_model(),
        tools=[],
        system_prompt="Answer in one short sentence. /no_think",
    )
    payload = {"messages": [{"role": "user", "content": "What is an Agent Harness?"}]}
    updates = list(agent.stream(payload, stream_mode="updates", version="v2"))
    assert updates
    print(f"STREAM_UPDATES_COUNT={len(updates)}")
    print(f"STREAM_UPDATES_FIRST={str(updates[0])[:400]}")
    print("STREAM_UPDATES=PASS")

    message_parts = list(agent.stream(payload, stream_mode="messages", version="v2"))
    assert message_parts
    print(f"STREAM_MESSAGES_COUNT={len(message_parts)}")
    print(f"STREAM_MESSAGES_FIRST={str(message_parts[0])[:300]}")
    print("STREAM_MESSAGES=PASS")


def pii_agent() -> None:
    seen_by_model: list[str] = []

    @wrap_model_call
    def observe_input(request, handler):
        seen_by_model.extend(str(message.content) for message in request.messages)
        return handler(request)

    agent = create_agent(
        model=create_local_model(),
        tools=[],
        system_prompt="Acknowledge briefly. /no_think",
        middleware=[
            PIIMiddleware("email", strategy="redact", apply_to_input=True),
            PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
            observe_input,
        ],
    )
    agent.invoke(
        {"messages": [{"role": "user", "content": f"Email {FAKE_EMAIL}; card {FAKE_CARD}."}]}
    )
    joined = "\n".join(seen_by_model)
    assert joined and FAKE_EMAIL not in joined and FAKE_CARD not in joined
    print(f"MODEL_INPUT_AFTER_PII={joined!r}")
    print("PII_BEFORE_MODEL=PASS")


def run() -> None:
    stream_agent()
    pii_agent()


if __name__ == "__main__":
    run()
