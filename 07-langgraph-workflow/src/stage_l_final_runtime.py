"""Stage L: one small workflow demonstrates observe, pause, inspect, replay, fork."""

from langgraph.types import Command

from stage_c_checkpointer import config
from stage_k_multi_agent_hitl_time_travel import build_graph


def run() -> dict[str, object]:
    graph = build_graph()
    thread = config("final-risk")
    stream = graph.stream_events({"query": "risk synthetic resource"}, config=thread, version="v3")
    values = list(stream.values)
    assert stream.interrupted and stream.interrupts[0].value["type"] == "approval"
    snapshot = graph.get_state(thread)
    assert snapshot.next == ("approval",) and snapshot.values["route"] == "risky"
    assert values
    resumed = graph.invoke(Command(resume=True), thread)
    assert resumed["worker_result"] == "SIMULATED_RISKY_WRITE"
    history = list(graph.get_state_history(thread))
    before_approval = next(item for item in history if item.next == ("approval",))
    assert graph.invoke(None, before_approval.config)["__interrupt__"]
    rejected_replay = graph.invoke(Command(resume=False), thread)
    assert rejected_replay["worker_result"] == "SIMULATED_SAFE_FALLBACK"

    route_thread = config("final-route")
    progress = list(graph.stream({"query": "record please"}, route_thread,
                                 stream_mode=["updates", "custom"], version="v2"))
    assert any(part["type"] == "custom" for part in progress)
    original = graph.get_state(route_thread)
    before_worker = next(item for item in graph.get_state_history(route_thread) if item.next == ("record_worker",))
    fork_config = graph.update_state(before_worker.config, {"route": "doctor"}, as_node="router")
    forked = graph.invoke(None, fork_config)
    assert original.values["final_answer"] == "record:synthetic record summary"
    assert forked["final_answer"] == "doctor:synthetic doctor summary"
    assert graph.get_state(original.config).values == original.values
    print(f"pause={snapshot.next}; resume={resumed['worker_result']}; replay={rejected_replay['worker_result']}")
    print(f"original={original.values['final_answer']}; fork={forked['final_answer']}")
    print("FINAL_RUNTIME_PASS")
    return {"graph": graph, "pause": snapshot, "resumed": resumed, "replay": rejected_replay,
            "original": original, "forked": forked, "progress": progress, "history": history}


if __name__ == "__main__":
    run()
