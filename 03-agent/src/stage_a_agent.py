"""Stage A: inspect a real local create_agent conversation and its system prompt."""

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langchain_core.messages import AIMessage, HumanMessage

from model_factory import create_local_model, local_chat_config


SYSTEM_PROMPT = "You are an IT teacher. Answer briefly and accurately. /no_think"


def run() -> None:
    seen_system_prompts: list[str] = []

    @wrap_model_call
    def observe_request(request, handler):
        seen_system_prompts.append(str(request.system_message.content))
        return handler(request)

    agent = create_agent(
        model=create_local_model(),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        middleware=[observe_request],
    )
    result = agent.invoke({"messages": [{"role": "user", "content": "What can you help me learn?"}]})
    messages = result["messages"]
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[-1], AIMessage) and messages[-1].content
    assert seen_system_prompts and SYSTEM_PROMPT in seen_system_prompts[0]
    base_url, model_id = local_chat_config()
    print(f"LOCAL_MODEL={model_id} BASE_URL={base_url}")
    print(f"SYSTEM_PROMPT_SEEN_BY_MODEL={seen_system_prompts[0]!r}")
    print(f"MESSAGE_TYPES={[type(message).__name__ for message in messages]}")
    print(f"FINAL_AI_MESSAGE={messages[-1].content}")
    print("CREATE_AGENT_CHAT=PASS")


if __name__ == "__main__":
    run()
