"""The smallest deterministic graph used to learn runtime streaming."""

from typing_extensions import TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph


class RuntimeState(TypedDict):
    query: str
    route: str
    result: str


def build_graph():
    def router(state: RuntimeState) -> dict[str, str]:
        return {"route": "worker"}

    def worker(state: RuntimeState) -> dict[str, str]:
        writer = get_stream_writer()
        writer({"stage": "worker", "status": "started"})
        result = f"handled:{state['query']}"
        writer({"stage": "worker", "status": "finished"})
        return {"result": result}

    builder = StateGraph(RuntimeState)
    builder.add_node("router", router)
    builder.add_node("worker", worker)
    builder.add_edge(START, "router")
    builder.add_edge("router", "worker")
    builder.add_edge("worker", END)
    return builder.compile()


def initial_state() -> RuntimeState:
    return {"query": "hello", "route": "", "result": ""}
