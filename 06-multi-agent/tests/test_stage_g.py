from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from supervisor import invoke_supervisor


class FakeSupervisor:
    def invoke(self, input_state):
        return {"messages": [
            HumanMessage(content="two domains"),
            AIMessage(content="", tool_calls=[
                {"name": "ask_record_agent", "args": {"task": "record"}, "id": "1"},
                {"name": "ask_doctor_agent", "args": {"task": "doctor"}, "id": "2"},
            ]),
            ToolMessage(content="SYNTHETIC RECORDS", tool_call_id="1", name="ask_record_agent"),
            ToolMessage(content="SYNTHETIC DIRECTORY", tool_call_id="2", name="ask_doctor_agent"),
            AIMessage(content="two results"),
        ]}


def test_multi_subagent_message_loop_extraction():
    result = invoke_supervisor(FakeSupervisor(), "two domains")
    assert {call["name"] for call in result["calls"]} == {"ask_record_agent", "ask_doctor_agent"}
    assert len(result["tool_messages"]) == 2 and result["final"] == "two results"
