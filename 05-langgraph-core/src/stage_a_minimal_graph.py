"""A: StateGraph builds a graph; compile() makes it executable."""

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


class TextState(TypedDict):
    text: str


def build_graph(order: list[str] | None = None) -> CompiledStateGraph:
    def step_a(state: TextState) -> dict:
        if order is not None:
            order.append("A")
        return {"text": state["text"] + " -> A"}

    def step_b(state: TextState) -> dict:
        if order is not None:
            order.append("B")
        return {"text": state["text"] + " -> B"}

    builder = StateGraph(TextState)
    builder.add_node("step_a", step_a)
    builder.add_node("step_b", step_b)
    builder.add_edge(START, "step_a")
    builder.add_edge("step_a", "step_b")
    builder.add_edge("step_b", END)
    assert isinstance(builder, StateGraph)
    graph = builder.compile()
    assert isinstance(graph, CompiledStateGraph)
    return graph


def run() -> None:
    order: list[str] = []
    graph = build_graph(order)
    input_state = {"text": "START"}
    result = graph.invoke(input_state)
    print(f"INPUT={input_state}")
    print(f"EXECUTION_ORDER={order}")
    print(f"BUILDER=StateGraph COMPILED={type(graph).__name__}")
    print(f"FINAL_STATE={result}")
    assert order == ["A", "B"]
    assert result == {"text": "START -> A -> B"}
    print("MINIMAL_GRAPH_PASS")


if __name__ == "__main__":
    run()
