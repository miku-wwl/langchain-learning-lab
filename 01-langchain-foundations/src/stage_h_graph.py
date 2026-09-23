"""Stage H: a deterministic two-node LangGraph preview."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class NumberState(TypedDict):
    value: int
    visited: Annotated[list[str], operator.add]


def increment(state: NumberState) -> dict:
    return {"value": state["value"] + 1, "visited": ["increment"]}


def double(state: NumberState) -> dict:
    return {"value": state["value"] * 2, "visited": ["double"]}


def build_graph():
    builder = StateGraph(NumberState)
    builder.add_node("increment", increment)
    builder.add_node("double", double)
    builder.add_edge(START, "increment")
    builder.add_edge("increment", "double")
    builder.add_edge("double", END)
    return builder.compile()


def run() -> None:
    result = build_graph().invoke({"value": 20, "visited": []})
    print(f"GRAPH_STATE={result}")
    assert result == {"value": 42, "visited": ["increment", "double"]}
    print("LANGGRAPH_COMPILE_INVOKE=PASS")


if __name__ == "__main__":
    run()
