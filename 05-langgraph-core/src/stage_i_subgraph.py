"""I: A parent graph invokes a subgraph over one shared reducer channel."""

import operator
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class SharedState(TypedDict):
    log: Annotated[list[str], operator.add]


def build_subgraph():
    def sub_step(state: SharedState) -> dict:
        return {"log": ["subgraph"]}

    builder = StateGraph(SharedState)
    builder.add_node("sub_step", sub_step)
    builder.add_edge(START, "sub_step")
    builder.add_edge("sub_step", END)
    return builder.compile()


def build_graph():
    def parent_step(state: SharedState) -> dict:
        return {"log": ["parent"]}

    child = build_subgraph()

    def invoke_child(state: SharedState) -> dict:
        # Both graphs append to log. Pass an empty child log so only its delta
        # crosses back to the parent's reducer; replaying the parent log doubles it.
        result = child.invoke({"log": []})
        return {"log": result["log"]}

    builder = StateGraph(SharedState)
    builder.add_node("parent_step", parent_step)
    builder.add_node("child", invoke_child)
    builder.add_edge(START, "parent_step")
    builder.add_edge("parent_step", "child")
    builder.add_edge("child", END)
    return builder.compile()


def run() -> None:
    result = build_graph().invoke({"log": []})
    assert result["log"] == ["parent", "subgraph"], result
    print(f"SUBGRAPH_LOG={result['log']}")
    print("SUBGRAPH_PASS")


if __name__ == "__main__":
    run()
