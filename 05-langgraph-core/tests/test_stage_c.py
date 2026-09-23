from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState

from stage_c_reducers import CustomMessageState, build_aggregation_graph, build_messages_graph


def test_reducer_aggregation_and_plain_overwrite():
    assert build_aggregation_graph().invoke({"values": [], "status": "start"}) == {
        "values": [10, 20], "status": "B"
    }


def test_messages_state_and_custom_add_messages():
    initial = {"messages": [HumanMessage(content="hi", id="request-1")]}
    for schema in (MessagesState, CustomMessageState):
        messages = build_messages_graph(schema).invoke(initial)["messages"]
        assert [type(message) for message in messages] == [HumanMessage, AIMessage]
        assert [message.content for message in messages] == ["hi", "hello"]
