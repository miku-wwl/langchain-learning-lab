"""E: conditional edges branch and can point backward; a guard bounds loops."""

from typing import Literal

from typing_extensions import TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph


class RouteState(TypedDict):
    number: int
    result: str


class CountState(TypedDict):
    count: int


def build_routing_graph():
    def classify(state: RouteState) -> dict:
        return {}  # The routing function reads the existing number.

    def route(state: RouteState) -> Literal["positive", "negative"]:
        return "positive" if state["number"] >= 0 else "negative"

    builder = StateGraph(RouteState)
    builder.add_node("classify", classify)
    builder.add_node("positive", lambda state: {"result": "positive"})
    builder.add_node("negative", lambda state: {"result": "negative"})
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route)
    builder.add_edge("positive", END)
    builder.add_edge("negative", END)
    return builder.compile()


def build_counting_graph(always_continue: bool = False):
    def increment(state: CountState) -> dict:
        return {"count": state["count"] + 1}

    def continue_or_end(state: CountState) -> Literal["increment", "__end__"]:
        return "increment" if always_continue or state["count"] < 3 else END

    builder = StateGraph(CountState)
    builder.add_node("increment", increment)
    builder.add_edge(START, "increment")
    builder.add_conditional_edges("increment", continue_or_end)
    return builder.compile()


def run() -> None:
    routing = build_routing_graph()
    positive = routing.invoke({"number": 5, "result": ""})
    negative = routing.invoke({"number": -5, "result": ""})
    print(f"POSITIVE={positive} NEGATIVE={negative}")
    assert positive["result"] == "positive" and negative["result"] == "negative"
    print("CONDITIONAL_ROUTING_PASS")

    count = build_counting_graph().invoke({"count": 0})
    print(f"LOOP_FINAL={count}")
    assert count == {"count": 3}
    print("LOOP_PASS")

    try:
        build_counting_graph(always_continue=True).invoke(
            {"count": 0}, config={"recursion_limit": 4}
        )
    except GraphRecursionError as error:
        print(f"RECURSION_GUARD={type(error).__name__}")
    else:
        raise AssertionError("an endless loop escaped recursion_limit")
    print("RECURSION_GUARD_PASS")


if __name__ == "__main__":
    run()
