"""H: Command combines a state update with a routing decision."""

from typing import Literal

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class ScoreState(TypedDict):
    score: int
    result: str
    destination: str


def build_graph():
    def decide(state: ScoreState) -> Command[Literal["pass_node", "fail_node"]]:
        if state["score"] >= 60:
            return Command(update={"result": "pass"}, goto="pass_node")
        return Command(update={"result": "fail"}, goto="fail_node")

    def pass_node(state: ScoreState) -> dict:
        assert state["result"] == "pass"
        return {"destination": "pass_node"}

    def fail_node(state: ScoreState) -> dict:
        assert state["result"] == "fail"
        return {"destination": "fail_node"}

    builder = StateGraph(ScoreState)
    builder.add_node("decide", decide)
    builder.add_node("pass_node", pass_node)
    builder.add_node("fail_node", fail_node)
    builder.add_edge(START, "decide")
    builder.add_edge("pass_node", END)
    builder.add_edge("fail_node", END)
    return builder.compile()


def run() -> None:
    graph = build_graph()
    passed = graph.invoke({"score": 80, "result": "", "destination": ""})
    failed = graph.invoke({"score": 40, "result": "", "destination": ""})
    assert (passed["result"], passed["destination"]) == ("pass", "pass_node")
    assert (failed["result"], failed["destination"]) == ("fail", "fail_node")
    print(f"COMMAND_PASS_PATH={passed} COMMAND_FAIL_PATH={failed}")
    print("COMMAND_PASS")


if __name__ == "__main__":
    run()
