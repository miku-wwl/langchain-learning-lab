"""Stage F: simulated approve and reject through interrupt/resume."""

from typing_extensions import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from stage_c_checkpointer import config


class ApprovalState(TypedDict):
    request: str
    prepared: NotRequired[bool]
    approved: NotRequired[bool]
    result: NotRequired[str]


def build_graph():
    def prepare(state: ApprovalState) -> dict:
        return {"prepared": True}

    def approval(state: ApprovalState) -> dict:
        decision = interrupt({"type": "approval", "question": f"Approve {state['request']}?"})
        return {"approved": bool(decision)}

    def execute(state: ApprovalState) -> dict:
        return {"result": "SIMULATED_WRITE"}

    def stop(state: ApprovalState) -> dict:
        return {"result": "REJECTED"}

    builder = StateGraph(ApprovalState)
    for name, node in (("prepare", prepare), ("approval", approval), ("execute", execute), ("stop", stop)):
        builder.add_node(name, node)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "approval")
    builder.add_conditional_edges("approval", lambda state: "execute" if state["approved"] else "stop")
    builder.add_edge("execute", END)
    builder.add_edge("stop", END)
    return builder.compile(checkpointer=InMemorySaver())


def run() -> dict[str, object]:
    graph = build_graph()
    results = {}
    for thread_id, decision, expected in (("hitl-approve", True, "SIMULATED_WRITE"), ("hitl-reject", False, "REJECTED")):
        paused = graph.invoke({"request": "synthetic write"}, config(thread_id))
        assert len(paused["__interrupt__"]) == 1
        payload = paused["__interrupt__"][0].value
        assert payload["type"] == "approval"
        assert graph.get_state(config(thread_id)).next == ("approval",)
        print(f"thread={thread_id} paused={payload}")
        results[thread_id] = graph.invoke(Command(resume=decision), config(thread_id))
        assert results[thread_id]["result"] == expected
        assert graph.get_state(config(thread_id)).next == ()
    assert graph.get_state(config("different-thread")).values == {}
    print("HITL_INTERRUPT_PASS")
    print("HITL_APPROVE_PASS")
    print("HITL_REJECT_PASS")
    return {"graph": graph, "results": results}


if __name__ == "__main__":
    run()
