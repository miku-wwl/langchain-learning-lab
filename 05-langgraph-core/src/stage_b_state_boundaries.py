"""B: external input/output schemas hide internal working state."""

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class InputState(TypedDict):
    user_input: str


class OverallState(TypedDict):
    user_input: str
    working_text: str
    graph_output: str


class OutputState(TypedDict):
    graph_output: str


def build_graph(observed: list[dict] | None = None):
    def prepare(state: InputState) -> dict:
        update = {"working_text": state["user_input"].strip()}
        if observed is not None:
            observed.append({"node": "prepare", "update": update})
        return update

    def process(state: OverallState) -> dict:
        update = {"graph_output": state["working_text"].upper()}
        if observed is not None:
            observed.append({"node": "process", "update": update})
        return update

    builder = StateGraph(
        OverallState, input_schema=InputState, output_schema=OutputState
    )
    builder.add_node("prepare", prepare)
    builder.add_node("process", process)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "process")
    builder.add_edge("process", END)
    return builder.compile()


def run() -> None:
    observed: list[dict] = []
    result = build_graph(observed).invoke({"user_input": "  langgraph  "})
    print(f"PARTIAL_UPDATES={observed}")
    print(f"EXTERNAL_OUTPUT={result}")
    assert observed == [
        {"node": "prepare", "update": {"working_text": "langgraph"}},
        {"node": "process", "update": {"graph_output": "LANGGRAPH"}},
    ]
    assert result == {"graph_output": "LANGGRAPH"}
    print("STATE_BOUNDARY_PASS")


if __name__ == "__main__":
    run()
