"""G: Send creates distinct runtime tasks and a reducer joins their results."""

import operator
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class OverallState(TypedDict):
    subjects: list[str]
    results: Annotated[list[str], operator.add]


class WorkerInput(TypedDict):
    subject: str


def build_graph(observed: list[str] | None = None):
    def fan_out(state: OverallState) -> dict:
        return {}

    def dispatch(state: OverallState) -> list[Send]:
        return [Send("process", {"subject": subject}) for subject in state["subjects"]]

    def process(state: WorkerInput) -> dict:
        if observed is not None:
            observed.append(state["subject"])
        return {"results": [f"processed:{state['subject']}"]}

    builder = StateGraph(OverallState)
    builder.add_node("fan_out", fan_out)
    builder.add_node("process", process)
    builder.add_edge(START, "fan_out")
    builder.add_conditional_edges("fan_out", dispatch, ["process"])
    builder.add_edge("process", END)
    return builder.compile()


def run() -> None:
    observed: list[str] = []
    result = build_graph(observed).invoke({"subjects": ["A", "B", "C"], "results": []})
    expected = {"processed:A", "processed:B", "processed:C"}
    assert set(observed) == {"A", "B", "C"} and len(observed) == 3
    assert set(result["results"]) == expected and len(result["results"]) == 3
    print(f"SEND_TASKS={observed} REDUCED_RESULTS={result['results']}")
    print("SEND_FANOUT_PASS")


if __name__ == "__main__":
    run()
