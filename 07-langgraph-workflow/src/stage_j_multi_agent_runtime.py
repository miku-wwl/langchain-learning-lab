"""Stage J: a tiny router/worker workflow with streamed progress and checkpoints."""

from typing_extensions import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph

from stage_c_checkpointer import config


class MultiState(TypedDict):
    query: str
    route: NotRequired[str]
    worker_result: NotRequired[str]
    final_answer: NotRequired[str]
    approved: NotRequired[bool]


def route(state: MultiState) -> str:
    return "record" if "record" in state["query"] else "doctor"


def router(state: MultiState) -> dict:
    selected = route(state)
    get_stream_writer()({"agent": "router", "status": "selected", "route": selected})
    return {"route": selected}


def record_worker(state: MultiState) -> dict:
    writer = get_stream_writer()
    writer({"agent": "record_worker", "status": "started"})
    writer({"agent": "record_worker", "status": "finished"})
    return {"worker_result": "synthetic record summary"}


def doctor_worker(state: MultiState) -> dict:
    writer = get_stream_writer()
    writer({"agent": "doctor_worker", "status": "started"})
    writer({"agent": "doctor_worker", "status": "finished"})
    return {"worker_result": "synthetic doctor summary"}


def aggregate(state: MultiState) -> dict:
    get_stream_writer()({"agent": "aggregate", "status": "finished"})
    return {"final_answer": f"{state['route']}:{state['worker_result']}"}


def build_graph():
    builder = StateGraph(MultiState)
    for name, node in (("router", router), ("record_worker", record_worker), ("doctor_worker", doctor_worker), ("aggregate", aggregate)):
        builder.add_node(name, node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", lambda state: state["route"], {"record": "record_worker", "doctor": "doctor_worker"})
    builder.add_edge("record_worker", "aggregate")
    builder.add_edge("doctor_worker", "aggregate")
    builder.add_edge("aggregate", END)
    return builder.compile(checkpointer=InMemorySaver())


def run() -> dict[str, object]:
    graph = build_graph()
    chunks = list(graph.stream({"query": "record please"}, config("multi-j"), stream_mode=["updates", "custom"], version="v2"))
    updates = [part["data"] for part in chunks if part["type"] == "updates"]
    custom = [part["data"] for part in chunks if part["type"] == "custom"]
    assert updates[0] == {"router": {"route": "record"}}
    assert "record_worker" in updates[1]
    assert "aggregate" in updates[2]
    assert [(item["agent"], item["status"]) for item in custom] == [
        ("router", "selected"), ("record_worker", "started"),
        ("record_worker", "finished"), ("aggregate", "finished")
    ]
    snapshot = graph.get_state(config("multi-j"))
    assert snapshot.values["final_answer"] == "record:synthetic record summary"
    assert snapshot.next == () and len(list(graph.get_state_history(config("multi-j")))) >= 4
    print(f"updates={updates}; progress={custom}")
    print("MULTI_AGENT_STREAMING_PASS")
    print("MULTI_AGENT_PERSISTENCE_PASS")
    return {"graph": graph, "updates": updates, "custom": custom, "snapshot": snapshot}


if __name__ == "__main__":
    run()
