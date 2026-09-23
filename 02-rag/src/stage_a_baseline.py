"""Stage A: ask the local model without giving it any company documents."""

from model_factory import create_local_chat_model, local_chat_config


def run() -> None:
    base_url, model_id = local_chat_config()
    print(f"CHAT_MODEL={model_id} BASE_URL={base_url}")
    response = create_local_chat_model().invoke(
        "What is Northstar Shop's exact refund deadline after delivery? "
        "Answer only if you know its internal policy."
    )
    assert response.content, "local model returned empty content"
    print(f"BASELINE_ANSWER={response.content}")
    print("BASELINE_LOCAL_MODEL=PASS")


if __name__ == "__main__":
    run()
