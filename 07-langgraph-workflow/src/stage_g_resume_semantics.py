"""Stage G: resume restarts a node; action placement matters."""

from typing_extensions import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from stage_c_checkpointer import config


class State(TypedDict):
    approved: NotRequired[bool]
    result: NotRequired[str]


def run() -> dict[str, object]:
    bad_events: list[str] = []
    good_events: list[str] = []
    approval_node_runs = 0

    def bad_approval(state: State) -> dict:
        nonlocal approval_node_runs
        approval_node_runs += 1
        bad_events.append("SIMULATED_BEFORE_APPROVAL")
        return {"approved": bool(interrupt("approve synthetic action?"))}

    bad_builder = StateGraph(State)
    bad_builder.add_node("approval", bad_approval)
    bad_builder.add_edge(START, "approval")
    bad_builder.add_edge("approval", END)
    bad_graph = bad_builder.compile(checkpointer=InMemorySaver())
    paused = bad_graph.invoke({}, config("bad"))
    assert paused["__interrupt__"] and approval_node_runs == 1
    bad_graph.invoke(Command(resume=True), config("bad"))
    assert approval_node_runs == 2 and len(bad_events) == 2

    def good_approval(state: State) -> dict:
        return {"approved": bool(interrupt("approve synthetic action?"))}

    def action(state: State) -> dict:
        good_events.append("SIMULATED_AFTER_APPROVAL")
        return {"result": "SIMULATED_ACTION"}

    builder = StateGraph(State)
    builder.add_node("approval", good_approval)
    builder.add_node("action", action)
    builder.add_edge(START, "approval")
    builder.add_conditional_edges("approval", lambda state: "action" if state["approved"] else END)
    builder.add_edge("action", END)
    good_graph = builder.compile(checkpointer=InMemorySaver())
    assert good_graph.invoke({}, config("good"))["__interrupt__"]
    final = good_graph.invoke(Command(resume=True), config("good"))
    assert final["result"] == "SIMULATED_ACTION" and len(good_events) == 1
    print(f"approval_node_runs={approval_node_runs}; bad_events={len(bad_events)}; good_events={len(good_events)}")
    print("RESUME_REEXECUTION_PASS")
    print("SIDE_EFFECT_BOUNDARY_PASS")
    return {"approval_node_runs": approval_node_runs, "bad_events": bad_events, "good_events": good_events}


if __name__ == "__main__":
    run()
