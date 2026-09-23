"""Stage K: approval for a synthetic risky worker and route fork."""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from stage_c_checkpointer import config
from stage_j_multi_agent_runtime import MultiState, aggregate, doctor_worker, record_worker, router


def build_graph():
    def extended_router(state: MultiState) -> dict:
        if "risk" in state["query"]:
            return {"route": "risky"}
        return router(state)

    def approval(state: MultiState) -> dict:
        return {"approved": bool(interrupt({"type": "approval", "route": state["route"]}))}

    def risky_worker(state: MultiState) -> dict:
        return {"worker_result": "SIMULATED_RISKY_WRITE"}

    def fallback(state: MultiState) -> dict:
        return {"worker_result": "SIMULATED_SAFE_FALLBACK"}

    builder = StateGraph(MultiState)
    for name, node in (("router", extended_router), ("record_worker", record_worker),
                       ("doctor_worker", doctor_worker), ("approval", approval),
                       ("risky_worker", risky_worker), ("fallback", fallback), ("aggregate", aggregate)):
        builder.add_node(name, node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", lambda state: state["route"],
                                  {"record": "record_worker", "doctor": "doctor_worker", "risky": "approval"})
    builder.add_conditional_edges("approval", lambda state: "risky_worker" if state["approved"] else "fallback")
    for name in ("record_worker", "doctor_worker", "risky_worker", "fallback"):
        builder.add_edge(name, "aggregate")
    builder.add_edge("aggregate", END)
    return builder.compile(checkpointer=InMemorySaver())


def run() -> dict[str, object]:
    graph = build_graph()
    outcomes = {}
    for thread_id, decision, expected in (("risk-approve", True, "SIMULATED_RISKY_WRITE"),
                                          ("risk-reject", False, "SIMULATED_SAFE_FALLBACK")):
        stream = graph.stream_events({"query": "risk synthetic resource"}, config=config(thread_id), version="v3")
        assert stream.interrupted
        assert stream.interrupts[0].value == {"type": "approval", "route": "risky"}
        resumed = graph.stream_events(Command(resume=decision), config=config(thread_id), version="v3")
        outcomes[thread_id] = resumed.output
        assert not resumed.interrupted
        assert outcomes[thread_id]["worker_result"] == expected
    print(f"HITL outcomes={[(key, value['worker_result']) for key, value in outcomes.items()]}")

    # Replaying a checkpoint before approval asks for a fresh decision.
    before_approval = next(s for s in graph.get_state_history(config("risk-approve")) if s.next == ("approval",))
    replay_pause = graph.invoke(None, before_approval.config)
    assert replay_pause["__interrupt__"]
    replay_reject = graph.invoke(Command(resume=False), config("risk-approve"))
    assert replay_reject["worker_result"] == "SIMULATED_SAFE_FALLBACK"
    print("Time travel before approval interrupted again")
    print("MULTI_AGENT_HITL_PASS")

    original = graph.invoke({"query": "record please"}, config("route-fork"))
    original_snapshot = graph.get_state(config("route-fork"))
    before_worker = next(s for s in graph.get_state_history(config("route-fork")) if s.next == ("record_worker",))
    fork_config = graph.update_state(before_worker.config, {"route": "doctor"}, as_node="router")
    forked = graph.invoke(None, fork_config)
    assert original["final_answer"] == "record:synthetic record summary"
    assert forked["final_answer"] == "doctor:synthetic doctor summary"
    assert graph.get_state(original_snapshot.config).values["final_answer"] == original["final_answer"]
    print(f"original={original['final_answer']}; fork={forked['final_answer']}")
    print("MULTI_AGENT_FORK_PASS")
    return {"graph": graph, "outcomes": outcomes, "original": original, "forked": forked}


if __name__ == "__main__":
    run()
