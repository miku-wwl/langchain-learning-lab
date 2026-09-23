"""Stage C: a checkpointed, thread-scoped counter workflow."""

from typing_extensions import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class CounterState(TypedDict):
    increment: int
    total: NotRequired[int]
    current_step: NotRequired[str]
    workflow_state: NotRequired[str]
    messages: NotRequired[list[str]]


def config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def build_graph():
    def add(state: CounterState) -> dict:
        return {"total": state.get("total", 0) + state["increment"], "current_step": "added"}

    def finish(state: CounterState) -> dict:
        return {"workflow_state": "complete", "messages": [f"total={state['total']}"]}

    builder = StateGraph(CounterState)
    builder.add_node("add", add)
    builder.add_node("finish", finish)
    builder.add_edge(START, "add")
    builder.add_edge("add", "finish")
    builder.add_edge("finish", END)
    return builder.compile(checkpointer=InMemorySaver())


def run() -> dict[str, object]:
    graph = build_graph()
    first = graph.invoke({"increment": 2}, config("thread-a"))
    second = graph.invoke({"increment": 3}, config("thread-a"))
    other = graph.invoke({"increment": 7}, config("thread-b"))
    assert first["total"] == 2 and second["total"] == 5
    assert other["total"] == 7
    assert graph.get_state(config("thread-a")).values["total"] == 5
    assert graph.get_state(config("thread-b")).values["total"] == 7
    checkpoints = list(graph.stream({"increment": 1}, config("checkpoint-events"), stream_mode="checkpoints", version="v2"))
    assert checkpoints
    print(f"thread-a totals=2,5; thread-b total={other['total']}")
    print(f"checkpoint stream events={len(checkpoints)}")
    print("CHECKPOINTER_PASS")
    print("THREAD_ISOLATION_PASS")
    return {"graph": graph, "first": first, "second": second, "other": other}


if __name__ == "__main__":
    run()
