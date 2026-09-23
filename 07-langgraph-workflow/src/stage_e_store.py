"""Stage E: shared Store data and isolated checkpoint state."""

from typing_extensions import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore

from stage_c_checkpointer import config


class StoreState(TypedDict):
    thread_label: str
    preference: NotRequired[str]


def build_graph(store: InMemoryStore):
    def read_preference(state: StoreState, runtime: Runtime) -> dict:
        item = runtime.store.get(("users", "user_123"), "preference")
        return {"preference": item.value["style"]}

    builder = StateGraph(StoreState)
    builder.add_node("read_preference", read_preference)
    builder.add_edge(START, "read_preference")
    builder.add_edge("read_preference", END)
    return builder.compile(checkpointer=InMemorySaver(), store=store)


def run() -> dict[str, object]:
    store = InMemoryStore()
    store.put(("users", "user_123"), "preference", {"style": "concise"})
    graph = build_graph(store)
    a = graph.invoke({"thread_label": "a"}, config("store-a"))
    b = graph.invoke({"thread_label": "b"}, config("store-b"))
    assert a["preference"] == b["preference"] == "concise"
    assert graph.get_state(config("store-a")).values["thread_label"] == "a"
    assert graph.get_state(config("store-b")).values["thread_label"] == "b"
    print(f"shared preference={a['preference']}; checkpoint labels=a,b")
    print("CHECKPOINTER_STORE_BOUNDARY_PASS")
    return {"graph": graph, "store": store, "a": a, "b": b}


if __name__ == "__main__":
    run()
