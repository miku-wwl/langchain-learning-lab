"""C: plain fields overwrite; reducers combine updates, including messages."""

import operator
from typing import Annotated

from typing_extensions import TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages


class AggregationState(TypedDict):
    values: Annotated[list[int], operator.add]
    status: str


class CustomMessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def build_aggregation_graph():
    builder = StateGraph(AggregationState)
    builder.add_node("first", lambda state: {"values": [10], "status": "A"})
    builder.add_node("second", lambda state: {"values": [20], "status": "B"})
    builder.add_edge(START, "first")
    builder.add_edge("first", "second")
    builder.add_edge("second", END)
    return builder.compile()


def build_messages_graph(state_schema=MessagesState):
    def reply(state: MessagesState) -> dict:
        assert len(state["messages"]) == 1
        return {"messages": [AIMessage(content="hello", id="reply-1")]}

    builder = StateGraph(state_schema)
    builder.add_node("reply", reply)
    builder.add_edge(START, "reply")
    builder.add_edge("reply", END)
    return builder.compile()


def run() -> None:
    aggregate = build_aggregation_graph().invoke({"values": [], "status": "start"})
    initial = {"messages": [HumanMessage(content="hi", id="request-1")]}
    messages = build_messages_graph().invoke(initial)["messages"]
    custom = build_messages_graph(CustomMessageState).invoke(initial)["messages"]
    print(f"AGGREGATED_STATE={aggregate}")
    print(f"MESSAGES_STATE={[type(item).__name__ for item in messages]}")
    print(f"CUSTOM_ADD_MESSAGES={[item.content for item in custom]}")
    assert aggregate == {"values": [10, 20], "status": "B"}
    assert [type(item) for item in messages] == [HumanMessage, AIMessage]
    assert [item.content for item in custom] == ["hi", "hello"]
    print("REDUCER_PASS")


if __name__ == "__main__":
    run()
