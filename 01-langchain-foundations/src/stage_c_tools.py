"""Stage C: define and bind tools; inspect the model's first tool call."""

from model_factory import create_local_model
from tools import ADD_EXECUTIONS, add, get_current_date


def run() -> None:
    assert add.invoke({"a": 17, "b": 25}) == 42
    assert get_current_date.invoke({})
    assert ADD_EXECUTIONS[-1] == (17, 25)
    print(f"TOOL_SCHEMA={add.args_schema.model_json_schema()}")

    model = create_local_model().bind_tools([add])
    message = model.invoke(
        "Use the add tool to calculate 17 + 25. Return the tool result."
    )
    print(f"MODEL_CONTENT={message.content}")
    print(f"MODEL_METADATA={message.additional_kwargs}")
    print(f"TOOL_CALLS={message.tool_calls}")
    assert message.tool_calls, "model did not produce a tool call"
    call = message.tool_calls[0]
    assert call["name"] == "add", call
    assert call["args"]["a"] + call["args"]["b"] == 42, call
    print("BOUND_MODEL_PRODUCED_TOOL_CALL=PASS")


if __name__ == "__main__":
    run()
