"""Stage B: turn template variables into messages, then invoke the model."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from model_factory import create_local_model


def translation_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", "Translate the following from English into {language}."),
            ("user", "{text}"),
        ]
    )


def run() -> None:
    prompt = translation_prompt().invoke(
        {"language": "Chinese", "text": "Hello, how are you?"}
    )
    assert isinstance(prompt.messages[0], SystemMessage)
    assert isinstance(prompt.messages[1], HumanMessage)
    assert "Chinese" in prompt.messages[0].content
    assert prompt.messages[1].content == "Hello, how are you?"
    print(f"PROMPT={prompt.messages}")

    reply = create_local_model().invoke(prompt)
    assert reply.content, "prompted model returned empty content"
    print(f"RESPONSE={reply.content}")
    print("PROMPT_TEMPLATE=PASS")


if __name__ == "__main__":
    run()
