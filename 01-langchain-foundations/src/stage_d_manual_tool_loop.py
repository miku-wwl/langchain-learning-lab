"""Stage D: perform the exact tool loop hidden inside an agent runtime."""

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from model_factory import create_local_model
from tools import ADD_EXECUTIONS, add


TOOLS_BY_NAME = {add.name: add}


def dispatch_tool_call(call: dict) -> ToolMessage:
    tool = TOOLS_BY_NAME[call["name"]]
    result = tool.invoke(call)
    assert isinstance(result, ToolMessage)
    return result


def run() -> None:
    model = create_local_model().bind_tools([add])
    messages = [
        SystemMessage(content="Use the add tool for arithmetic. After its result, give the number only."),
        HumanMessage(content="Calculate 17 + 25 using the add tool."),
    ]
    before = len(ADD_EXECUTIONS)
    first_reply = model.invoke(messages)
    messages.append(first_reply)
    assert first_reply.tool_calls, "model did not request the tool"
    print(f"AI_TOOL_CALLS={first_reply.tool_calls}")

    for call in first_reply.tool_calls:
        tool_message = dispatch_tool_call(call)
        messages.append(tool_message)
        print(f"TOOL_MESSAGE={tool_message.content} TOOL_CALL_ID={tool_message.tool_call_id}")

    assert len(ADD_EXECUTIONS) > before, "Python tool was not executed"
    assert any(isinstance(m, ToolMessage) and m.content == "42" for m in messages)

    final_reply = model.invoke(messages)
    messages.append(final_reply)
    assert not final_reply.tool_calls, "model requested another tool instead of answering"
    assert "42" in str(final_reply.content), final_reply.content
    print(f"FINAL_ANSWER={final_reply.content}")
    print("MANUAL_TOOL_LOOP=PASS")


if __name__ == "__main__":
    run()
