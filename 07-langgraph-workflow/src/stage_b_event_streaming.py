"""Stage B: typed v3 projections and a named nested graph."""

from langgraph.graph import END, START, StateGraph

from runtime_graph import RuntimeState, build_graph, initial_state


def build_nested_graph():
    child = StateGraph(RuntimeState)
    child.add_node("child_worker", lambda state: {"result": f"nested:{state['query']}"})
    child.add_edge(START, "child_worker")
    child.add_edge("child_worker", END)
    child_graph = child.compile(name="demo_child")

    parent = StateGraph(RuntimeState)
    parent.add_node("router", lambda state: {"route": "child"})
    parent.add_node("child", child_graph)
    parent.add_edge(START, "router")
    parent.add_edge("router", "child")
    parent.add_edge("child", END)
    return parent.compile(name="demo_parent")


def run() -> dict[str, object]:
    tasks = list(build_graph().stream(initial_state(), stream_mode="tasks", version="v2"))
    debug = list(build_graph().stream(initial_state(), stream_mode="debug", version="v2"))
    assert tasks and debug
    print(f"Raw tasks={len(tasks)} debug={len(debug)}")
    stream = build_graph().stream_events(initial_state(), version="v3")
    values = list(stream.values)
    output = stream.output
    assert output["result"] == "handled:hello"
    assert any(value.get("route") == "worker" for value in values)
    assert values[-1]["result"] == output["result"]
    print(f"Typed values={len(values)} output={output}")

    nested = build_nested_graph().stream_events(initial_state(), version="v3")
    subgraphs = [(subgraph.graph_name, subgraph.path) for subgraph in nested.subgraphs]
    assert nested.output["result"] == "nested:hello"
    print(f"Subgraphs={subgraphs}")
    # The embedded node is reported as "child" in LangGraph 1.2.12.
    assert any(name == "child" and path for name, path in subgraphs)
    print("EVENT_STREAM_PASS")
    return {"values": values, "output": output, "subgraphs": subgraphs}


if __name__ == "__main__":
    run()
