"""J: compare state snapshots, partial updates, custom data and task events."""

from typing_extensions import TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph


class StreamState(TypedDict):
    value: int


def build_graph():
    def increment(state: StreamState) -> dict:
        return {"value": state["value"] + 1}

    def double(state: StreamState) -> dict:
        get_stream_writer()({"progress": "doubling"})
        return {"value": state["value"] * 2}

    builder = StateGraph(StreamState)
    builder.add_node("increment", increment)
    builder.add_node("double", double)
    builder.add_edge(START, "increment")
    builder.add_edge("increment", "double")
    builder.add_edge("double", END)
    return builder.compile()


def run() -> None:
    graph = build_graph()
    updates = list(graph.stream({"value": 1}, stream_mode="updates"))
    assert updates == [{"increment": {"value": 2}}, {"double": {"value": 4}}]
    print(f"STREAM_UPDATES={updates}")
    print("STREAM_UPDATES_PASS")

    values = list(graph.stream({"value": 1}, stream_mode="values"))
    assert [item["value"] for item in values] == [1, 2, 4]
    print(f"STREAM_VALUES={values}")
    print("STREAM_VALUES_PASS")

    custom = list(graph.stream({"value": 1}, stream_mode="custom"))
    assert custom == [{"progress": "doubling"}]
    print(f"STREAM_CUSTOM={custom}")
    print("STREAM_CUSTOM_PASS")

    tasks = list(graph.stream({"value": 1}, stream_mode="tasks"))
    assert any(event.get("name") == "increment" for event in tasks)
    assert any(event.get("name") == "double" for event in tasks)
    print(f"STREAM_TASKS={tasks}")
    print("STREAM_TASKS_PASS")


if __name__ == "__main__":
    run()
