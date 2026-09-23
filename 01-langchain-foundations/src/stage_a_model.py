"""Stage A: real invoke, ainvoke, and streaming against a local model."""

import asyncio

from langchain.chat_models import init_chat_model

from model_factory import create_local_model, local_model_config


async def run() -> None:
    base_url, model_id = local_model_config()
    model = create_local_model()
    print(f"LOCAL_MODEL={model_id} BASE_URL={base_url}")

    reply = model.invoke("Say hello in one short sentence.")
    assert reply.content, "invoke returned empty content"
    print(f"INVOKE={reply.content}")

    initialized = init_chat_model(
        model_id,
        model_provider="openai",
        base_url=base_url,
        api_key="local",
        temperature=0,
        max_tokens=64,
    )
    initialized_reply = initialized.invoke("Reply with one short greeting.")
    assert initialized_reply.content, "init_chat_model returned empty content"
    print(f"INIT_CHAT_MODEL={initialized_reply.content}")

    async_reply = await model.ainvoke("Say your name in one short sentence.")
    assert async_reply.content, "ainvoke returned empty content"
    print(f"AINVOKE={async_reply.content}")

    chunks = list(model.stream("Write a short greeting."))
    streamed = "".join(str(chunk.content) for chunk in chunks)
    assert chunks and streamed.strip(), "stream returned no text"
    print(f"STREAM_CHUNKS={len(chunks)} STREAM_TEXT={streamed}")
    print("MODEL_INVOKE_ASYNC_STREAM=PASS")


if __name__ == "__main__":
    asyncio.run(run())
